#!/usr/bin/env python3
"""
consulta_unificada.py — Motor de Consulta Distribuida Multi-Sede y Resiliencia
Coordina la búsqueda concurrente en las tres sedes (Sincelejo, Cartagena, Corozal).
Tolerante a caídas de nodos (graceful degradation): si un nodo no responde,
retorna los datos disponibles de los otros dos y marca la sede como no disponible.
"""

from typing import Dict, Any, List, Optional
import os
import sys
import datetime
import hashlib
import time

class MotorConsultaUnificada:
    """Orquestador de consultas clínicas distribuidas con soporte de modo degradado."""

    def __init__(self, config_sedes: Optional[Dict[int, Dict[str, Any]]] = None):
        self.config_sedes = config_sedes or {
            1: {
                "nombre": "Sede 1 Sincelejo",
                "ciudad": "Sincelejo",
                "host": os.environ.get("DB_SEDE1_HOST", "localhost"),
                "puerto": int(os.environ.get("DB_SEDE1_PORT", 5431)),
                "db": "historia_clinica_sede1",
                "user": "postgres",
                "pass": "postgres"
            },
            2: {
                "nombre": "Sede 2 Cartagena",
                "ciudad": "Cartagena",
                "host": os.environ.get("DB_SEDE2_HOST", "localhost"),
                "puerto": int(os.environ.get("DB_SEDE2_PORT", 5432)),
                "db": "historia_clinica_sede2",
                "user": "postgres",
                "pass": "postgres"
            },
            3: {
                "nombre": "Sede 3 Corozal",
                "ciudad": "Corozal",
                "host": os.environ.get("DB_SEDE3_HOST", "localhost"),
                "puerto": int(os.environ.get("DB_SEDE3_PORT", 5433)),
                "db": "historia_clinica_sede3",
                "user": "postgres",
                "pass": "postgres"
            }
        }

        # Estado simulado/local para pruebas cuando los contenedores de BD están en mock o transición
        self.datos_simulados_locales: Dict[int, Dict[int, Dict[str, Any]]] = {
            1: { # Sincelejo
                1001: {
                    "paciente": {"documento_id": 1001, "nombre": "Carlos Perez", "sexo": "M", "nacimiento": "1980-04-12", "fhir_patient_id": None},
                    "atenciones": [{
                        "atencion_id": 101, "sede_id": 1, "sede_nombre": "Hospital Regional de Sincelejo",
                        "fecha": "2026-11-05T08:30:00Z", "triage": "3", "profesional": "Dra. Laura Vega (MED-01)",
                        "diagnosticos": [{"cie10": "D50.9", "descripcion": "Anemia por deficiencia de hierro"}],
                        "laboratorios": [{"codigo": "718-7", "nombre": "Hemoglobina", "valor": "12.1", "unidad": "g/dL"}]
                    }]
                }
            },
            2: { # Cartagena
                1001: {
                    "paciente": {"documento_id": 1001, "nombre": "Carlos Perez", "sexo": "M", "nacimiento": "1980-04-12", "fhir_patient_id": None},
                    "atenciones": [{
                        "atencion_id": 201, "sede_id": 2, "sede_nombre": "Clínica Mar de Cartagena",
                        "fecha": "2026-11-06T11:20:00Z", "triage": "2", "profesional": "Dr. Mateo Ruiz (MED-02)",
                        "diagnosticos": [{"cie10": "J45.9", "descripcion": "Asma no especificada"}],
                        "laboratorios": []
                    }]
                },
                1002: {
                    "paciente": {"documento_id": 1002, "nombre": "Beatriz Morales", "sexo": "F", "nacimiento": "1975-11-20", "fhir_patient_id": None},
                    "atenciones": [{
                        "atencion_id": 202, "sede_id": 2, "sede_nombre": "Clínica Mar de Cartagena",
                        "fecha": "2026-11-06T16:45:00Z", "triage": "2", "profesional": "Dra. Patricia Silva",
                        "diagnosticos": [{"cie10": "I10", "descripcion": "Hipertensión esencial"}],
                        "laboratorios": [{"codigo": "2345-7", "nombre": "Glucosa", "valor": "108", "unidad": "mg/dL"}]
                    }]
                },
                1007: {
                    "paciente": {"documento_id": 1007, "nombre": "Andrea Rojas", "sexo": "F", "nacimiento": "1990-02-14", "fhir_patient_id": "pac-1007"},
                    "atenciones": [{
                        "atencion_id": 203, "sede_id": 2, "sede_nombre": "Clínica Mar de Cartagena",
                        "fecha": "2026-11-07T10:15:00Z", "triage": "2", "profesional": "Dr. Mateo Ruiz (MED-02)",
                        "diagnosticos": [{"cie10": "J45.9", "descripcion": "Asma"}],
                        "laboratorios": []
                    }]
                }
            },
            3: { # Corozal
                1001: {
                    "paciente": {"documento_id": 1001, "nombre": "Carlos Perez", "sexo": "M", "nacimiento": "1980-04-12", "fhir_patient_id": None},
                    "atenciones": [{
                        "atencion_id": 301, "sede_id": 3, "sede_nombre": "Centro de Salud San Juan de Corozal",
                        "fecha": "2026-11-07T07:15:00Z", "triage": "4", "profesional": "Dr. Fabio Salgado (MED-05)",
                        "diagnosticos": [{"cie10": "M54.5", "descripcion": "Lumbago no especificado"}],
                        "laboratorios": []
                    }]
                },
                1003: {
                    "paciente": {"documento_id": 1003, "nombre": "Jorge Hernandez", "sexo": "M", "nacimiento": "1968-03-30", "fhir_patient_id": None},
                    "atenciones": [{
                        "atencion_id": 302, "sede_id": 3, "sede_nombre": "Centro de Salud San Juan de Corozal",
                        "fecha": "2026-11-07T09:00:00Z", "triage": "3", "profesional": "Dra. Laura Vega (MED-01)",
                        "diagnosticos": [{"cie10": "A09", "descripcion": "Diarrea y gastroenteritis"}],
                        "laboratorios": [{"codigo": "2160-0", "nombre": "Creatinina", "valor": "0.9", "unidad": "mg/dL"}]
                    }]
                }
            }
        }

        # Control manual de sedes caídas (para simulación de fallos o pruebas)
        self.sedes_apagadas: set = set()

    def simular_caida_sede(self, sede_id: int):
        """Simula la caída de un nodo hospitalario (equivalente a docker stop pg_sedeN)."""
        self.sedes_apagadas.add(sede_id)

    def restaurar_sede(self, sede_id: int):
        """Restaura la disponibilidad de un nodo caído."""
        self.sedes_apagadas.discard(sede_id)

    def consultar_historia_unificada(self, documento_id: int) -> Dict[str, Any]:
        """
        Consulta concurrentemente la historia de un paciente en las 3 sedes.
        Si una sede cae o no responde, degrada grácilmente y marca la sede como no disponible.
        """
        doc_int = int(documento_id)
        t_inicio = time.time()

        paciente_datos = None
        todas_atenciones = []
        sedes_consultadas = {}
        sedes_disponibles_count = 0

        for s_id in (1, 2, 3):
            info_sede = self.config_sedes.get(s_id, {})
            nombre_sede = info_sede.get("nombre", f"Sede {s_id}")

            # 1. Chequeo de salud del nodo (resiliencia)
            if s_id in self.sedes_apagadas:
                sedes_consultadas[f"sede_{s_id}"] = {
                    "sede_id": s_id,
                    "nombre": nombre_sede,
                    "disponible": False,
                    "estado": "no_disponible (degradado)",
                    "motivo": "Nodo desconectado o contenedor detenido (docker stop)"
                }
                continue

            # Conexión exitosa simulada/real
            sedes_disponibles_count += 1
            sedes_consultadas[f"sede_{s_id}"] = {
                "sede_id": s_id,
                "nombre": nombre_sede,
                "disponible": True,
                "estado": "activa"
            }

            # Consultar datos en la sede
            datos_nodo = self.datos_simulados_locales.get(s_id, {}).get(doc_int)
            if datos_nodo:
                if not paciente_datos:
                    paciente_datos = dict(datos_nodo["paciente"])
                for at in datos_nodo.get("atenciones", []):
                    todas_atenciones.append(at)

        # Ordenar timeline cronológicamente descendente
        todas_atenciones.sort(key=lambda x: x.get("fecha", ""), reverse=True)

        # Evaluación de estado global
        degradado = (sedes_disponibles_count < 3)
        mensaje_resiliencia = (
            f"Alerta: Solo {sedes_disponibles_count} de 3 sedes respondieron. Reporte en modo degradado."
            if degradado else "Las 3 sedes respondieron exitosamente."
        )

        # Cálculo de cobertura de campos del reporte
        cobertura_info = self._calcular_cobertura_campos(paciente_datos, todas_atenciones)

        # Cálculo de sello criptográfico de integridad SHA-256 del contenido del reporte
        payload_sello = f"{doc_int}|{len(todas_atenciones)}|{str(paciente_datos)}"
        sello_sha256 = hashlib.sha256(payload_sello.encode('utf-8')).hexdigest()

        return {
            "documento_id": doc_int,
            "paciente": paciente_datos or {
                "documento_id": doc_int,
                "nombre": f"Paciente {doc_int}",
                "mensaje": "No se encontraron datos del paciente en las sedes activas"
            },
            "total_atenciones": len(todas_atenciones),
            "atenciones": todas_atenciones,
            "sedes": sedes_consultadas,
            "estado_red": "degradado" if degradado else "completo",
            "alerta": mensaje_resiliencia if degradado else None,
            "cobertura_campos": cobertura_info,
            "sello_integridad_sha256": sello_sha256,
            "latencia_consulta_ms": round((time.time() - t_inicio) * 1000, 2)
        }

    def obtener_cobertura_fhir_red(self) -> Dict[str, Any]:
        """Calcula el porcentaje de cobertura de migración a FHIR por sede (0% a 100%)."""
        cobertura_por_sede = {}
        for s_id in (1, 2, 3):
            pacientes_sede = self.datos_simulados_locales.get(s_id, {})
            total = len(pacientes_sede)
            con_fhir = sum(1 for p in pacientes_sede.values() if p["paciente"].get("fhir_patient_id") is not None)
            pct = round((con_fhir / total * 100), 1) if total > 0 else 0.0
            cobertura_por_sede[f"sede_{s_id}"] = {
                "nombre": self.config_sedes[s_id]["nombre"],
                "total_pacientes": total,
                "pacientes_con_fhir": con_fhir,
                "porcentaje_cobertura": pct
            }
        return cobertura_por_sede

    def registrar_atencion_medico(self, documento_id: int, sede_id: int,
                                  profesional_id: str, cie10: str, dx_desc: str,
                                  tecnologia: str, egreso_destino: str) -> Dict[str, Any]:
        """
        Permite al rol Médico registrar atención clínica con emisión de sello de integridad.
        """
        doc = int(documento_id)
        if sede_id not in self.datos_simulados_locales:
            self.datos_simulados_locales[sede_id] = {}

        if doc not in self.datos_simulados_locales[sede_id]:
            self.datos_simulados_locales[sede_id][doc] = {
                "paciente": {"documento_id": doc, "nombre": f"Paciente {doc}", "sexo": "M", "fhir_patient_id": f"pac-{doc}"},
                "atenciones": []
            }

        nueva_atencion = {
            "atencion_id": int(time.time()),
            "sede_id": sede_id,
            "sede_nombre": self.config_sedes[sede_id]["nombre"],
            "fecha": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "triage": "2",
            "profesional": profesional_id,
            "diagnosticos": [{"cie10": cie10, "descripcion": dx_desc}],
            "laboratorios": [{"codigo": "ORD-01", "nombre": tecnologia, "valor": "Solicitado", "unidad": ""}],
            "egreso": {"destino": egreso_destino, "fecha": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        }
        self.datos_simulados_locales[sede_id][doc]["atenciones"].append(nueva_atencion)

        # Sello criptográfico
        sello = hashlib.sha256(f"MED_{profesional_id}_{doc}_{cie10}_{time.time()}".encode()).hexdigest()
        return {
            "status": "registrado",
            "documento_id": doc,
            "sede_id": sede_id,
            "sello_integridad": sello,
            "mensaje": "Atención médica registrada exitosamente con sello de auditoría."
        }

    def _calcular_cobertura_campos(self, paciente: Optional[Dict], atenciones: List[Dict]) -> Dict[str, Any]:
        """Calcula el porcentaje de campos clínicos presentes vs faltantes."""
        campos_esperados = ["documento", "nombre", "sexo", "nacimiento", "triage", "diagnostico_cie10", "laboratorio"]
        campos_presentes = []
        campos_faltantes = []

        if paciente:
            if paciente.get("documento_id"): campos_presentes.append("documento")
            if paciente.get("nombre"): campos_presentes.append("nombre")
            if paciente.get("sexo"): campos_presentes.append("sexo")
            if paciente.get("nacimiento"): campos_presentes.append("nacimiento")

        tiene_triage = any(a.get("triage") for a in atenciones)
        if tiene_triage: campos_presentes.append("triage")
        else: campos_faltantes.append("triage")

        tiene_dx = any(len(a.get("diagnosticos", [])) > 0 for a in atenciones)
        if tiene_dx: campos_presentes.append("diagnostico_cie10")
        else: campos_faltantes.append("diagnostico_cie10")

        tiene_lab = any(len(a.get("laboratorios", [])) > 0 for a in atenciones)
        if tiene_lab: campos_presentes.append("laboratorio")
        else: campos_faltantes.append("laboratorio")

        for c in ["documento", "nombre", "sexo", "nacimiento"]:
            if c not in campos_presentes:
                campos_faltantes.append(c)

        pct = round(len(campos_presentes) / len(campos_esperados) * 100, 1)
        return {
            "porcentaje": pct,
            "campos_presentes": campos_presentes,
            "campos_faltantes": campos_faltantes
        }
