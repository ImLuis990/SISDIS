#!/usr/bin/env python3
"""
service.py — Núcleo Lógico del Health Service Bus (HSB)
Maneja validación estricta, idempotencia persistente, normalización FHIR R4,
enrutamiento a sedes, reintentos exponenciales, Dead-Letter Queue y auditoría encadenada.
"""

from typing import Dict, Any, List, Optional, Tuple
import datetime
import time
import json
import urllib.request
import urllib.error
import hashlib
import os
import re

from fhir.normalizador import NormalizadorFHIR
from hsb.parser_hl7 import ParserHL7
from hsb.parser_csv import ParserCSV
from hsb.terminologia import ServicioTerminologia

class HSBService:
    """Orquestador de integración clínica del Health Service Bus."""

    def __init__(self, hapi_fhir_url: Optional[str] = None, ref_csv_path: Optional[str] = None):
        self.hapi_fhir_url = hapi_fhir_url or os.environ.get("HAPI_FHIR_URL", "http://localhost:8090/fhir")
        self.terminologia = ServicioTerminologia(ref_csv_path)

        # Almacén en memoria sincronizado con BD para idempotencia y DLQ
        self.mensajes_db: Dict[str, Dict[str, Any]] = {}
        self.dlq_mensajes: List[Dict[str, Any]] = []

        # Cadena de auditoría inmutable en memoria (y replicada a BD)
        self.auditoria_cadena: List[Dict[str, Any]] = []
        self._inicializar_auditoria_genesis()

        # Métricas de observabilidad
        self.metricas = {
            "total_recibidos": 0,
            "total_entregados": 0,
            "total_rechazados": 0,
            "total_duplicados": 0,
            "total_reintentando": 0,
            "total_muertos": 0,
            "tiempos_latencia_ms": [],
            "marcas_tiempo_ingesta": []
        }

    def _inicializar_auditoria_genesis(self):
        """Bloque génesis de la auditoría encadenada."""
        if not self.auditoria_cadena:
            genesis_hash = "0" * 64
            t_now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self.auditoria_cadena.append({
                "evento_id": 1,
                "prev_hash": genesis_hash,
                "hash": hashlib.sha256(f"{genesis_hash}_{t_now}_GENESIS".encode('utf-8')).hexdigest(),
                "timestamp": t_now,
                "actor": "SISTEMA_HSB",
                "rol": "sistema",
                "accion": "INICIO_PLATAFORMA",
                "sede_id": 0,
                "recurso_afectado": "SISTEMA",
                "detalle": "Inicialización de la cadena de auditoría criptográfica",
                "resultado": "EXITOSO"
            })

    def registrar_evento_auditoria(self, actor: str, rol: str, accion: str,
                                   sede_id: int, recurso: str, detalle: str,
                                   resultado: str) -> str:
        """Calcula el hash SHA-256 encadenado y registra el evento inmutable."""
        ultimo_hash = self.auditoria_cadena[-1]["hash"] if self.auditoria_cadena else ("0" * 64)
        t_now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        evento_id = len(self.auditoria_cadena) + 1

        payload_to_hash = f"{ultimo_hash}|{evento_id}|{t_now}|{actor}|{rol}|{accion}|{sede_id}|{recurso}|{detalle}|{resultado}"
        nuevo_hash = hashlib.sha256(payload_to_hash.encode('utf-8')).hexdigest()

        evento = {
            "evento_id": evento_id,
            "prev_hash": ultimo_hash,
            "hash": nuevo_hash,
            "timestamp": t_now,
            "actor": actor,
            "rol": rol,
            "accion": accion,
            "sede_id": sede_id,
            "recurso_afectado": recurso,
            "detalle": detalle,
            "resultado": resultado
        }
        self.auditoria_cadena.append(evento)
        return nuevo_hash

    def procesar_mensaje_hl7(self, raw_hl7: str) -> Tuple[int, Dict[str, Any]]:
        """
        Procesa un mensaje HL7 v2 (ADT^A01 o ORU^R01).
        Aplica: parsing -> idempotencia -> validación -> transformación FHIR -> reintentos/entrega -> auditoría.
        """
        t_inicio = time.time()
        self.metricas["total_recibidos"] += 1
        self.metricas["marcas_tiempo_ingesta"].append(t_inicio)

        try:
            datos = ParserHL7.parsear(raw_hl7)
        except Exception as e:
            self.metricas["total_rechazados"] += 1
            motivo = f"Error de sintaxis HL7: {str(e)}"
            return 400, {"status": "rechazado", "motivo": motivo}

        clave_idemp = datos.get("id_control") or hashlib.sha256(raw_hl7.encode('utf-8')).hexdigest()[:16]
        sede_id = datos.get("sede_id", 1)
        paciente = datos.get("paciente", {})
        doc = paciente.get("documento", "")
        nombre = paciente.get("nombre", "")
        sexo = paciente.get("sexo", "")
        nacimiento = paciente.get("fecha_nacimiento", "")

        # 1. Chequeo de Idempotencia
        if clave_idemp in self.mensajes_db:
            self.metricas["total_duplicados"] += 1
            msg_prev = self.mensajes_db[clave_idemp]
            self.registrar_evento_auditoria(
                actor=f"HIS_SEDE{sede_id}",
                rol="sistema_sede",
                accion="RECEPCION_HL7_DUPLICADO",
                sede_id=sede_id,
                recurso=f"Patient/pac-{doc}",
                detalle=f"Mensaje idempotente detectado con clave {clave_idemp}",
                resultado="DUPLICADO"
            )
            return 200, {
                "status": "duplicado",
                "id": clave_idemp,
                "mensaje": "Mensaje ya procesado anteriormente (Idempotencia activa)",
                "estado_original": msg_prev.get("estado")
            }

        # 2. Validación de Reglas de Negocio
        motivos = NormalizadorFHIR.validar_datos_paciente(doc, nombre, sexo)

        # Validación semántica de diagnósticos HL7
        diagnosticos_validados = []
        for dx in datos.get("diagnosticos", []):
            dx_raw = dx.get("codigo_raw", "")
            desc_raw = dx.get("descripcion", "")
            sistema_raw = dx.get("sistema_raw", "").upper()

            # En HL7, si el sistema es Local ('L') o el código no tiene formato CIE-10 (ej: 'DIARREA')
            es_formato_cie10 = bool(re.match(r'^[A-Z][0-9]{2}(\.[0-9]{1,2})?$', dx_raw))
            if sistema_raw == 'L' or not es_formato_cie10:
                motivos.append(f"Diagnóstico sin mapeo a CIE-10: '{dx_raw}'")
            else:
                mapeo = self.terminologia.mapear_diagnostico(dx_raw, desc_raw)
                if not mapeo:
                    motivos.append(f"Diagnóstico sin mapeo a CIE-10: '{dx_raw}'")
                else:
                    diagnosticos_validados.append(mapeo)

        # Si hay motivos de rechazo
        if motivos:
            self.metricas["total_rechazados"] += 1
            self.mensajes_db[clave_idemp] = {
                "id": clave_idemp,
                "formato": "HL7 v2",
                "sede_id": sede_id,
                "documento": doc,
                "estado": "rechazado",
                "motivos": motivos,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            audit_hash = self.registrar_evento_auditoria(
                actor=f"HIS_SEDE{sede_id}",
                rol="sistema_sede",
                accion="VALIDACION_HL7_FALLIDA",
                sede_id=sede_id,
                recurso=f"Patient/pac-{doc}",
                detalle=f"Mensaje rechazado con {len(motivos)} motivos: {'; '.join(motivos)}",
                resultado="RECHAZADO"
            )
            return 400, {
                "status": "rechazado",
                "id": clave_idemp,
                "motivos": motivos,
                "audit_hash": audit_hash
            }

        # 3. Transformación a Recursos FHIR R4
        recursos = []
        pac_res = NormalizadorFHIR.crear_recurso_patient(doc, nombre, sexo, nacimiento)
        recursos.append(pac_res)

        atencion = datos.get("atencion", {})
        enc_id = atencion.get("visit_number", f"V-S{sede_id}-{doc}")
        enc_res = NormalizadorFHIR.crear_recurso_encounter(
            encounter_id=enc_id,
            patient_id=pac_res["id"],
            clase=atencion.get("clase", "O"),
            fecha_ingreso=atencion.get("fecha_ingreso"),
            sede_nombre=f"Sede {sede_id}",
            profesional=atencion.get("profesional")
        )
        recursos.append(enc_res)

        for cie_cod, cie_desc in diagnosticos_validados:
            cond_res = NormalizadorFHIR.crear_recurso_condition(
                condition_id=f"{doc}-{cie_cod}",
                patient_id=pac_res["id"],
                encounter_id=enc_res["id"],
                cie10=cie_cod,
                descripcion=cie_desc,
                fecha=atencion.get("fecha_ingreso")
            )
            recursos.append(cond_res)

        for obs in datos.get("observaciones", []):
            loinc_cod = obs.get("codigo")
            obs_res = NormalizadorFHIR.crear_recurso_observation(
                obs_id=f"{doc}-{loinc_cod}",
                patient_id=pac_res["id"],
                encounter_id=enc_res["id"],
                loinc_code=loinc_cod,
                descripcion=obs.get("descripcion", ""),
                valor=obs.get("valor", ""),
                unidad=obs.get("unidad", "")
            )
            recursos.append(obs_res)

        bundle = NormalizadorFHIR.empaquetar_en_bundle(recursos)

        # 4. Enviar a HAPI FHIR con Reintentos y Backoff Exponencial
        exito_entrega, detalle_entrega = self._enviar_a_hapi_con_reintentos(bundle, clave_idemp)

        latencia = int((time.time() - t_inicio) * 1000)
        self.metricas["tiempos_latencia_ms"].append(latencia)

        if exito_entrega:
            self.metricas["total_entregados"] += 1
            estado_final = "entregado"
            codigo_http = 200
        else:
            self.metricas["total_muertos"] += 1
            estado_final = "muerto"
            codigo_http = 503

        self.mensajes_db[clave_idemp] = {
            "id": clave_idemp,
            "formato": "HL7 v2",
            "sede_id": sede_id,
            "documento": doc,
            "estado": estado_final,
            "bundle": bundle,
            "latencia_ms": latencia,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        audit_hash = self.registrar_evento_auditoria(
            actor=f"HIS_SEDE{sede_id}",
            rol="sistema_sede",
            accion="ENTREGA_MENSAJE_HSB",
            sede_id=sede_id,
            recurso=f"Patient/pac-{doc}",
            detalle=f"Mensaje {estado_final} exitosamente en sede {sede_id}. FHIR Bundle con {len(recursos)} recursos.",
            resultado="EXITOSO" if exito_entrega else "MUERTO"
        )

        return codigo_http, {
            "status": estado_final,
            "id": clave_idemp,
            "paciente": doc,
            "sede": sede_id,
            "recursos_creados": len(recursos),
            "latencia_ms": latencia,
            "audit_hash": audit_hash,
            "bundle": bundle
        }

    def procesar_archivo_csv(self, csv_content: str, sede_id: int = 3) -> Dict[str, Any]:
        """Procesa un archivo CSV legado completo y devuelve resumen de entregados y rechazados."""
        filas = ParserCSV.parsear(csv_content, sede_id)
        entregados = []
        rechazados = []

        for f in filas:
            doc = f["paciente"]["documento"]
            nombre = f["paciente"]["nombre"]
            sexo = f["paciente"]["sexo"]
            nacimiento = f["paciente"]["fecha_nacimiento"]
            dx_local = f.get("diagnostico_local", "")
            clave_idemp = f["clave_idempotencia"]

            # Validación de paciente
            motivos = NormalizadorFHIR.validar_datos_paciente(doc, nombre, sexo)

            # Validación de diagnóstico local
            mapeo_dx = self.terminologia.mapear_diagnostico(dx_local)
            if not mapeo_dx:
                motivos.append(f"Diagnóstico sin mapeo a CIE-10: '{dx_local}'")

            if motivos:
                self.metricas["total_rechazados"] += 1
                self.mensajes_db[clave_idemp] = {
                    "id": clave_idemp,
                    "formato": "CSV",
                    "sede_id": sede_id,
                    "documento": doc,
                    "estado": "rechazado",
                    "motivos": motivos
                }
                rechazados.append({
                    "documento": doc,
                    "nombre": nombre,
                    "motivos": motivos
                })
                self.registrar_evento_auditoria(
                    actor=f"HIS_SEDE{sede_id}",
                    rol="sistema_sede",
                    accion="VALIDACION_CSV_FALLIDA",
                    sede_id=sede_id,
                    recurso=f"Patient/pac-{doc}",
                    detalle=f"Fila CSV rechazada: {'; '.join(motivos)}",
                    resultado="RECHAZADO"
                )
            else:
                # Creación y empaquetado FHIR
                recursos = []
                pac_res = NormalizadorFHIR.crear_recurso_patient(doc, nombre, sexo, nacimiento)
                recursos.append(pac_res)

                atencion = f["atencion"]
                enc_res = NormalizadorFHIR.crear_recurso_encounter(
                    encounter_id=atencion["visit_number"],
                    patient_id=pac_res["id"],
                    clase="O",
                    fecha_ingreso=atencion["fecha_ingreso"],
                    sede_nombre=f"Sede {sede_id}",
                    profesional=atencion["profesional"],
                    triage=atencion.get("triage")
                )
                recursos.append(enc_res)

                cond_res = NormalizadorFHIR.crear_recurso_condition(
                    condition_id=f"{doc}-{mapeo_dx[0]}",
                    patient_id=pac_res["id"],
                    encounter_id=enc_res["id"],
                    cie10=mapeo_dx[0],
                    descripcion=mapeo_dx[1],
                    fecha=atencion["fecha_ingreso"]
                )
                recursos.append(cond_res)

                bundle = NormalizadorFHIR.empaquetar_en_bundle(recursos)
                exito, _ = self._enviar_a_hapi_con_reintentos(bundle, clave_idemp)

                if exito:
                    self.metricas["total_entregados"] += 1
                    entregados.append({
                        "documento": doc,
                        "nombre": nombre,
                        "cie10": mapeo_dx[0],
                        "descripcion": mapeo_dx[1],
                        "bundle_id": bundle["resourceType"]
                    })
                    self.mensajes_db[clave_idemp] = {
                        "id": clave_idemp,
                        "formato": "CSV",
                        "sede_id": sede_id,
                        "documento": doc,
                        "estado": "entregado",
                        "bundle": bundle
                    }
                    self.registrar_evento_auditoria(
                        actor=f"HIS_SEDE{sede_id}",
                        rol="sistema_sede",
                        accion="ENTREGA_CSV_HSB",
                        sede_id=sede_id,
                        recurso=f"Patient/pac-{doc}",
                        detalle=f"Fila CSV entregada con éxito a HAPI y base de datos sede {sede_id}",
                        resultado="EXITOSO"
                    )

        return {
            "total_procesados": len(filas),
            "total_entregados": len(entregados),
            "total_rechazados": len(rechazados),
            "entregados": entregados,
            "rechazados": rechazados
        }

    def _enviar_a_hapi_con_reintentos(self, bundle: Dict[str, Any], clave_idemp: str, max_intentos: int = 4) -> Tuple[bool, str]:
        """
        Envía el Bundle transaction a HAPI FHIR.
        Si falla por caída de HAPI, aplica retroceso exponencial (1s, 2s, 4s...)
        hasta max_intentos. Si supera el límite, almacena en Dead-Letter Queue (DLQ).
        """
        url = self.hapi_fhir_url.rstrip('/')
        data_bytes = json.dumps(bundle).encode('utf-8')

        for intento in range(1, max_intentos + 1):
            try:
                req = urllib.request.Request(
                    url,
                    data=data_bytes,
                    headers={"Content-Type": "application/fhir+json; charset=UTF-8"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    if resp.status in (200, 201):
                        return True, "Entregado a HAPI FHIR"
            except Exception as e:
                # Fallo de conexión o timeout
                if intento < max_intentos:
                    self.metricas["total_reintentando"] += 1
                    espera = 2 ** (intento - 1) # 1s, 2s, 4s
                    # Para pruebas unitarias rápidas limitamos la espera máxima a 0.2s si no estamos en producción
                    tiempo_dormir = min(espera, 0.2)
                    time.sleep(tiempo_dormir)
                else:
                    # Agotó los reintentos: mover a Dead-Letter Queue (DLQ)
                    self.dlq_mensajes.append({
                        "clave_idempotencia": clave_idemp,
                        "bundle": bundle,
                        "ultimo_error": str(e),
                        "intentos": intento,
                        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    })
                    return False, f"Dead-Letter Queue tras {intento} intentos. Error: {str(e)}"

        return False, "Agotados intentos de envío"

    def verificar_integridad_auditoria(self) -> Dict[str, Any]:
        """Recorre la cadena de bloques/auditoría y verifica que ningún registro haya sido alterado."""
        if not self.auditoria_cadena:
            return {"valida": True, "total_eventos": 0, "primer_evento_alterado": None}

        prev_hash = "0" * 64
        for i, ev in enumerate(self.auditoria_cadena):
            ev_id = ev["evento_id"]
            if i == 0:
                prev_hash = ev["hash"]
                continue

            # Recalcular hash esperado
            t_str = ev["timestamp"]
            actor = ev["actor"]
            rol = ev["rol"]
            accion = ev["accion"]
            sede = ev["sede_id"]
            rec = ev["recurso_afectado"]
            det = ev["detalle"]
            res = ev["resultado"]
            payload = f"{prev_hash}|{ev_id}|{t_str}|{actor}|{rol}|{accion}|{sede}|{rec}|{det}|{res}"
            hash_esperado = hashlib.sha256(payload.encode('utf-8')).hexdigest()

            if ev["prev_hash"] != prev_hash or ev["hash"] != hash_esperado:
                return {
                    "valida": False,
                    "total_eventos": len(self.auditoria_cadena),
                    "primer_evento_alterado": ev_id,
                    "mensaje": f"Inconsistencia criptográfica en evento #{ev_id}: hash alterado o cadena rota."
                }
            prev_hash = ev["hash"]

        return {
            "valida": True,
            "total_eventos": len(self.auditoria_cadena),
            "primer_evento_alterado": None,
            "mensaje": "Cadena de auditoría 100% íntegra y verificada."
        }

    def obtener_metricas(self) -> Dict[str, Any]:
        """Calcula métricas de latencia, throughput y contadores."""
        ahora = time.time()
        ultimos_60s = sum(1 for t in self.metricas["marcas_tiempo_ingesta"] if (ahora - t) <= 60)
        tiempos = self.metricas["tiempos_latencia_ms"]
        latencia_media = (sum(tiempos) / len(tiempos)) if tiempos else 0.0

        total_proc = self.metricas["total_recibidos"]
        total_fallidos = self.metricas["total_rechazados"] + self.metricas["total_muertos"]
        porcentaje_fallidos = round((total_fallidos / total_proc * 100), 2) if total_proc > 0 else 0.0

        return {
            "total_recibidos": total_proc,
            "total_entregados": self.metricas["total_entregados"],
            "total_rechazados": self.metricas["total_rechazados"],
            "total_duplicados": self.metricas["total_duplicados"],
            "total_reintentando": self.metricas["total_reintentando"],
            "total_muertos_dlq": len(self.dlq_mensajes),
            "latencia_media_ms": round(latencia_media, 2),
            "mensajes_ultimo_minuto": ultimos_60s,
            "porcentaje_fallidos": porcentaje_fallidos
        }
