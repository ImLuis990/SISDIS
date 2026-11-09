#!/usr/bin/env python3
"""
parser_hl7.py — Parser de Mensajes HL7 v2 (ADT^A01 y ORU^R01)
Extrae segmentos MSH, PID, PV1, DG1, OBR y OBX según el estándar HL7 v2.5.
"""

from typing import Dict, Any, List, Optional

class ParserHL7:
    """Analizador léxico y sintáctico de mensajes HL7 v2 en texto plano."""

    @classmethod
    def parsear(cls, raw_content: str) -> Dict[str, Any]:
        """
        Analiza un mensaje HL7 v2 y extrae los campos clave.
        Soporta saltos de línea \\r, \\n o \\r\\n, así como segmentos consecutivos.
        """
        texto = raw_content.strip()
        if not texto:
            raise ValueError("Mensaje HL7 vacío")

        # Separar segmentos: HL7 tradicionalmente usa \r o \n
        lineas = re_split_segments(texto)
        segmentos: Dict[str, List[List[str]]] = {}

        for linea in lineas:
            linea_limpia = linea.strip()
            if not linea_limpia:
                continue
            campos = linea_limpia.split('|')
            tag = campos[0].strip()
            if tag not in segmentos:
                segmentos[tag] = []
            segmentos[tag].append(campos)

        if 'MSH' not in segmentos:
            raise ValueError("Mensaje HL7 inválido: no contiene segmento MSH")

        msh = segmentos['MSH'][0]
        # Nota sobre índices MSH: en MSH, el campo MSH-1 es '|'
        # Por tanto campos[1] es encoding characters (^~\&), campos[2] es MSH-3, campos[3] es MSH-4, etc.
        msh_sending_app = msh[2] if len(msh) > 2 else ""
        msh_sending_facility = msh[3] if len(msh) > 3 else ""
        msh_timestamp = msh[6] if len(msh) > 6 else ""
        msh_msg_type = msh[8] if len(msh) > 8 else ""
        msh_msg_control_id = msh[9] if len(msh) > 9 else ""

        # Determinar sede emisora (1, 2 o 3)
        sede_id = 1
        fac_upper = (msh_sending_facility or msh_sending_app).upper()
        if 'SEDE2' in fac_upper or 'CARTAGENA' in fac_upper:
            sede_id = 2
        elif 'SEDE3' in fac_upper or 'COROZAL' in fac_upper:
            sede_id = 3
        elif 'SEDE1' in fac_upper or 'SINCELEJO' in fac_upper:
            sede_id = 1

        resultado: Dict[str, Any] = {
            "tipo_mensaje": msh_msg_type,
            "id_control": msh_msg_control_id,
            "timestamp": msh_timestamp,
            "sede_id": sede_id,
            "sending_facility": msh_sending_facility,
            "paciente": {},
            "atencion": {},
            "diagnosticos": [],
            "observaciones": []
        }

        # Analizar PID (Patient Identification)
        if 'PID' in segmentos:
            pid = segmentos['PID'][0]
            # PID-3: Patient Identifier List (ej: 1007^^^HIS)
            doc_raw = pid[3] if len(pid) > 3 else ""
            documento = doc_raw.split('^')[0].strip()

            # PID-5: Patient Name (ej: Rojas^Andrea)
            nombre_raw = pid[5] if len(pid) > 5 else ""

            # PID-7: Date/Time of Birth (ej: 19900214)
            nacimiento = pid[7] if len(pid) > 7 else ""

            # PID-8: Administrative Sex (ej: F, M)
            sexo = pid[8] if len(pid) > 8 else ""

            resultado["paciente"] = {
                "documento": documento,
                "nombre": nombre_raw,
                "fecha_nacimiento": nacimiento,
                "sexo": sexo
            }

        # Analizar PV1 (Patient Visit)
        if 'PV1' in segmentos:
            pv1 = segmentos['PV1'][0]
            # PV1-2: Patient Class (O, E, I)
            patient_class = pv1[2] if len(pv1) > 2 else "O"

            # PV1-7: Attending Doctor (ej: MED-02^Ruiz^Mateo)
            medico = pv1[7] if len(pv1) > 7 else ""

            # PV1-19: Visit Number (ej: V-S2-0101)
            visit_number = pv1[19] if len(pv1) > 19 else f"V-S{sede_id}-{msh_msg_control_id}"

            # PV1-44: Admit Date/Time (ej: 202611071015)
            fecha_ingreso = pv1[44] if len(pv1) > 44 else msh_timestamp

            resultado["atencion"] = {
                "visit_number": visit_number,
                "clase": patient_class,
                "profesional": medico,
                "fecha_ingreso": fecha_ingreso
            }

        # Analizar DG1 (Diagnosis)
        if 'DG1' in segmentos:
            for dg1 in segmentos['DG1']:
                # DG1-3: Diagnosis Code-DG1 (ej: J45.9^Asma^I10 o DIARREA^Diarrea^L)
                dx_raw = dg1[3] if len(dg1) > 3 else ""
                partes_dx = dx_raw.split('^')
                codigo = partes_dx[0].strip() if len(partes_dx) > 0 else ""
                desc = partes_dx[1].strip() if len(partes_dx) > 1 else codigo
                sistema = partes_dx[2].strip() if len(partes_dx) > 2 else ""

                # DG1-5: Diagnosis Date/Time
                fecha_dx = dg1[5] if len(dg1) > 5 else msh_timestamp

                resultado["diagnosticos"].append({
                    "codigo_raw": codigo,
                    "descripcion": desc,
                    "sistema_raw": sistema,
                    "fecha": fecha_dx
                })

        # Analizar OBR y OBX (Observation Request and Results)
        if 'OBX' in segmentos:
            for obx in segmentos['OBX']:
                # OBX-2: Value Type (NM, ST, TX)
                tipo_valor = obx[2] if len(obx) > 2 else "ST"

                # OBX-3: Observation Identifier (ej: 718-7^Hemoglobina^LN)
                obs_id_raw = obx[3] if len(obx) > 3 else ""
                partes_obs = obs_id_raw.split('^')
                loinc_codigo = partes_obs[0].strip() if len(partes_obs) > 0 else ""
                obs_nombre = partes_obs[1].strip() if len(partes_obs) > 1 else loinc_codigo

                # OBX-5: Observation Value (ej: 13.8)
                valor = obx[5] if len(obx) > 5 else ""

                # OBX-6: Units (ej: g/dL)
                unidad = obx[6] if len(obx) > 6 else ""

                resultado["observaciones"].append({
                    "codigo": loinc_codigo,
                    "descripcion": obs_nombre,
                    "tipo_valor": tipo_valor,
                    "valor": valor,
                    "unidad": unidad
                })

        return resultado

def re_split_segments(text: str) -> List[str]:
    """Separa segmentos por retornos de carro o saltos de línea, o por marcas de segmento."""
    # Reemplazar retornos
    cleaned = text.replace('\r\n', '\n').replace('\r', '\n')
    # Manejar caso de HL7 en una sola línea donde los segmentos están pegados (ej: 'PID|...PV1|...')
    known_segments = ['MSH', 'PID', 'PV1', 'DG1', 'OBR', 'OBX', 'IN1']
    for seg in known_segments:
        cleaned = cleaned.replace(seg + '|', '\n' + seg + '|')
    lineas = [l for l in cleaned.split('\n') if l.strip()]
    return lineas
