#!/usr/bin/env python3
"""
normalizador.py — Normalizador a FHIR R4
Transforma datos clínicos (HL7 v2, CSV o registros relacionales) en recursos
Patient, Encounter, Condition (CIE-10) y Observation (LOINC) dentro de un
Bundle FHIR R4 de tipo transaction con PUT determinista.
"""

from typing import Dict, Any, List, Optional
import datetime
import re

class NormalizadorError(Exception):
    """Excepción generada ante violaciones de validación o normalización."""
    def __init__(self, message: str, motivos: Optional[List[str]] = None):
        super().__init__(message)
        self.motivos = motivos or [message]

class NormalizadorFHIR:
    """Motor de normalización y generación de recursos FHIR R4."""

    MAPEO_GENERO = {
        'M': 'male',
        'MASCULINO': 'male',
        'F': 'female',
        'FEMENINO': 'female',
        'O': 'other',
        'OTRO': 'other'
    }

    MAPEO_MODALIDAD_ENCOUNTER = {
        'O': ('AMB', 'ambulatory'),
        'E': ('EMER', 'emergency'),
        'I': ('IMP', 'inpatient encounter'),
        'URGENCIAS': ('EMER', 'emergency'),
        'AMBULATORIO': ('AMB', 'ambulatory'),
        'HOSPITALARIO': ('IMP', 'inpatient encounter'),
        'CONSULTA EXTERNA': ('AMB', 'ambulatory')
    }

    @classmethod
    def validar_datos_paciente(cls, documento: Any, nombre: str, sexo: str) -> List[str]:
        """Valida las reglas mínimas del paciente."""
        motivos = []
        doc_str = str(documento).strip() if documento is not None else ""
        
        # Regla 1: Documento numérico de entre 4 y 15 dígitos
        if not doc_str.isdigit():
            motivos.append("Documento no numérico")
        elif len(doc_str) < 4 or len(doc_str) > 15:
            motivos.append(f"Documento con longitud inválida ({len(doc_str)} dígitos, debe ser entre 4 y 15)")

        # Regla 2: Nombre no vacío
        if not nombre or not str(nombre).strip():
            motivos.append("Nombre del paciente no puede estar vacío")

        # Regla 3: Sexo válido
        sexo_normalizado = str(sexo).strip().upper() if sexo else ""
        if sexo_normalizado not in cls.MAPEO_GENERO:
            motivos.append(f"Sexo no válido ('{sexo}', debe ser M, F u O)")

        return motivos

    @classmethod
    def crear_recurso_patient(cls, documento: str, nombre_completo: str, 
                               sexo: str, fecha_nacimiento: Optional[str] = None) -> Dict[str, Any]:
        """Genera un recurso Patient FHIR R4 con ID determinista."""
        doc_clean = str(documento).strip()
        patient_id = f"pac-{doc_clean}"
        gender_code = cls.MAPEO_GENERO.get(str(sexo).strip().upper(), "unknown")

        # Separar apellidos y nombres si contiene sombrerito o espacios
        nombre_str = str(nombre_completo).strip()
        if '^' in nombre_str:
            partes = nombre_str.split('^')
            family = partes[0].strip()
            given = [p.strip() for p in partes[1:] if p.strip()]
        else:
            partes = nombre_str.split()
            if len(partes) >= 2:
                family = " ".join(partes[-2:]) if len(partes) >= 3 else partes[-1]
                given = partes[:-2] if len(partes) >= 3 else [partes[0]]
            else:
                family = nombre_str
                given = [nombre_str]

        # Formato de fecha de nacimiento (YYYY-MM-DD o YYYYMMDD)
        birth_date_str = None
        if fecha_nacimiento:
            f_str = str(fecha_nacimiento).strip()
            if len(f_str) == 8 and f_str.isdigit():
                birth_date_str = f"{f_str[:4]}-{f_str[4:6]}-{f_str[6:]}"
            elif '-' in f_str:
                birth_date_str = f_str.split('T')[0]

        patient = {
            "resourceType": "Patient",
            "id": patient_id,
            "identifier": [
                {
                    "use": "official",
                    "system": "urn:oid:co:minsalud:identificacion",
                    "value": doc_clean
                }
            ],
            "active": True,
            "name": [
                {
                    "use": "official",
                    "family": family,
                    "given": given if given else [family]
                }
            ],
            "gender": gender_code
        }
        if birth_date_str:
            patient["birthDate"] = birth_date_str

        return patient

    @classmethod
    def crear_recurso_encounter(cls, encounter_id: str, patient_id: str, 
                                 clase: str, fecha_ingreso: Optional[str] = None,
                                 sede_nombre: str = "Sede Hospitalaria",
                                 profesional: Optional[str] = None,
                                 triage: Optional[str] = None) -> Dict[str, Any]:
        """Genera un recurso Encounter FHIR R4 con ID determinista."""
        enc_id = f"enc-{str(encounter_id).replace('^', '-').replace('_', '-')}"
        class_info = cls.MAPEO_MODALIDAD_ENCOUNTER.get(str(clase).strip().upper(), ('AMB', 'ambulatory'))

        # Normalizar fecha a ISO 8601
        start_date = cls._normalizar_fecha_iso(fecha_ingreso)

        encounter = {
            "resourceType": "Encounter",
            "id": enc_id,
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": class_info[0],
                "display": class_info[1]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "serviceProvider": {
                "display": sede_nombre
            }
        }
        if start_date:
            encounter["period"] = {"start": start_date}

        if profesional:
            encounter["participant"] = [
                {
                    "individual": {
                        "display": str(profesional).replace('^', ' ')
                    }
                }
            ]

        if triage and str(triage).strip():
            encounter["priority"] = {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority",
                        "code": str(triage).strip(),
                        "display": f"Triage Nivel {triage}"
                    }
                ]
            }

        return encounter

    @classmethod
    def crear_recurso_condition(cls, condition_id: str, patient_id: str, encounter_id: str,
                                cie10: str, descripcion: str, fecha: Optional[str] = None) -> Dict[str, Any]:
        """Genera un recurso Condition FHIR R4 (Diagnóstico CIE-10)."""
        cond_id = f"cond-{str(condition_id).replace('.', '-')}"
        rec_date = cls._normalizar_fecha_iso(fecha)

        condition = {
            "resourceType": "Condition",
            "id": cond_id,
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                        "display": "Active"
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed",
                        "display": "Confirmed"
                    }
                ]
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": "encounter-diagnosis",
                            "display": "Encounter Diagnosis"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/icd-10",
                        "code": str(cie10).strip(),
                        "display": descripcion or cie10
                    }
                ],
                "text": descripcion or cie10
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "encounter": {
                "reference": f"Encounter/{encounter_id}"
            }
        }
        if rec_date:
            condition["recordedDate"] = rec_date

        return condition

    @classmethod
    def crear_recurso_observation(cls, obs_id: str, patient_id: str, encounter_id: str,
                                   loinc_code: str, descripcion: str, valor: Any, 
                                   unidad: str = "", fecha: Optional[str] = None) -> Dict[str, Any]:
        """Genera un recurso Observation FHIR R4 (Prueba de Laboratorio LOINC)."""
        clean_obs_id = f"obs-{str(obs_id).replace('.', '-')}"
        eff_date = cls._normalizar_fecha_iso(fecha)

        obs = {
            "resourceType": "Observation",
            "id": clean_obs_id,
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "laboratory",
                            "display": "Laboratory"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": str(loinc_code).strip(),
                        "display": descripcion or loinc_code
                    }
                ],
                "text": descripcion or loinc_code
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "encounter": {
                "reference": f"Encounter/{encounter_id}"
            }
        }
        if eff_date:
            obs["effectiveDateTime"] = eff_date

        # Convertir valor si es numérico
        val_str = str(valor).strip().replace(',', '.')
        try:
            val_num = float(val_str)
            obs["valueQuantity"] = {
                "value": val_num,
                "unit": unidad or "unidad",
                "system": "http://unitsofmeasure.org",
                "code": unidad or "1"
            }
        except ValueError:
            obs["valueString"] = str(valor)

        return obs

    @classmethod
    def empaquetar_en_bundle(cls, recursos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Empaqueta una lista de recursos FHIR en un Bundle de tipo 'transaction'
        con método HTTP PUT determinista para garantizar idempotencia total.
        """
        entries = []
        for res in recursos:
            res_type = res.get("resourceType")
            res_id = res.get("id")
            if not res_type or not res_id:
                continue

            entry = {
                "fullUrl": f"urn:uuid:{res_id}",
                "resource": res,
                "request": {
                    "method": "PUT",
                    "url": f"{res_type}/{res_id}"
                }
            }
            entries.append(entry)

        bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": entries
        }
        return bundle

    @staticmethod
    def _normalizar_fecha_iso(fecha_raw: Optional[str]) -> Optional[str]:
        """Convierte formatos YYYYMMDDHHMMSS o ISO a ISO 8601 con zona horaria."""
        if not fecha_raw:
            return None
        f = str(fecha_raw).strip()
        # Formato HL7: YYYYMMDDHHMMSS o YYYYMMDDHHMM
        if len(f) in (12, 14) and f.isdigit():
            y, m, d = f[0:4], f[4:6], f[6:8]
            h, mi = f[8:10], f[10:12]
            s = f[12:14] if len(f) == 14 else "00"
            return f"{y}-{m}-{d}T{h}:{mi}:{s}Z"
        elif len(f) == 8 and f.isdigit():
            return f"{f[0:4]}-{f[4:6]}-{f[6:8]}T00:00:00Z"
        elif 'T' in f:
            if not f.endswith('Z') and '+' not in f and '-' not in f[10:]:
                return f"{f}:00Z" if len(f.split('T')[1]) == 5 else f"{f}Z"
            return f
        elif '-' in f and len(f) == 10:
            return f"{f}T00:00:00Z"
        return f
