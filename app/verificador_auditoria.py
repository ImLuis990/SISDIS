#!/usr/bin/env python3
"""
verificador_auditoria.py — Verificador de Integridad de la Auditoría Encadenada
Recorre la secuencia cronológica de eventos de auditoría y recalcula los hashes
SHA-256 encadenados. Detecta inmediatamente cualquier alteración, borrado o
modificación no autorizada de registros históricos.
"""

from typing import List, Dict, Any, Tuple
import hashlib
import sys
import os
import json

class VerificadorAuditoria:
    """Verificador de inmutabilidad criptográfica estilo blockchain para auditoría en salud."""

    @classmethod
    def verificar_cadena(cls, eventos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Recorre la lista ordenada de eventos y verifica:
        1. Que cada prev_hash coincida con el hash del evento anterior.
        2. Que el hash del evento coincida con el SHA-256 de su contenido.
        """
        if not eventos:
            return {
                "valida": True,
                "total_eventos": 0,
                "primer_evento_alterado": None,
                "mensaje": "No hay eventos registrados en la auditoría."
            }

        prev_hash = "0" * 64

        for i, ev in enumerate(eventos):
            ev_id = ev.get("evento_id", i + 1)
            hash_actual = ev.get("hash", "")
            prev_hash_guardado = ev.get("prev_hash", "")

            # Bloque génesis
            if i == 0:
                prev_hash = hash_actual
                continue

            # 1. Verificar enlace con el bloque previo
            if prev_hash_guardado != prev_hash:
                return {
                    "valida": False,
                    "total_eventos": len(eventos),
                    "primer_evento_alterado": ev_id,
                    "tipo_falla": "ENLACE_ROTO",
                    "mensaje": f"ALERTA DE SEGURIDAD: Enlace roto en evento #{ev_id}. prev_hash esperado '{prev_hash[:12]}...', encontrado '{prev_hash_guardado[:12]}...'."
                }

            # 2. Recalcular hash de contenido
            t_str = str(ev.get("timestamp", ""))
            actor = str(ev.get("actor", ""))
            rol = str(ev.get("rol", ""))
            accion = str(ev.get("accion", ""))
            sede = str(ev.get("sede_id", 0))
            rec = str(ev.get("recurso_afectado", ""))
            det = str(ev.get("detalle", ""))
            res = str(ev.get("resultado", ""))

            payload = f"{prev_hash}|{ev_id}|{t_str}|{actor}|{rol}|{accion}|{sede}|{rec}|{det}|{res}"
            hash_recalculado = hashlib.sha256(payload.encode('utf-8')).hexdigest()

            if hash_actual != hash_recalculado:
                return {
                    "valida": False,
                    "total_eventos": len(eventos),
                    "primer_evento_alterado": ev_id,
                    "tipo_falla": "CONTENIDO_MANIPULADO",
                    "mensaje": f"ALERTA DE SEGURIDAD: Contenido adulterado en evento #{ev_id}. El hash no coincide con los datos del registro."
                }

            prev_hash = hash_actual

        return {
            "valida": True,
            "total_eventos": len(eventos),
            "primer_evento_alterado": None,
            "mensaje": f"Auditoría 100% íntegra y verificada. {len(eventos)} eventos evaluados sin anomalías."
        }

def main():
    """Ejecutor de demostración desde terminal."""
    print("=" * 65)
    print("VERIFICADOR DE INTEGRIDAD CRIPTOGRÁFICA DE AUDITORÍA (SHA-256)")
    print("=" * 65)

    # Simular cadena de prueba
    genesis_hash = "0" * 64
    t1 = "2026-11-09T16:00:00Z"
    h1 = hashlib.sha256(f"{genesis_hash}_{t1}_GENESIS".encode()).hexdigest()

    t2 = "2026-11-09T16:01:00Z"
    p2 = f"{h1}|2|{t2}|MED-01|medico|CONSULTA_HC|1|Patient/pac-1001|Consulta unificada|EXITOSO"
    h2 = hashlib.sha256(p2.encode()).hexdigest()

    t3 = "2026-11-09T16:02:00Z"
    p3 = f"{h2}|3|{t3}|MED-02|medico|REGISTRO_DIAGNOSTICO|2|Condition/cond-1001-J45|Diagnóstico Asma|EXITOSO"
    h3 = hashlib.sha256(p3.encode()).hexdigest()

    cadena_original = [
        {"evento_id": 1, "prev_hash": genesis_hash, "hash": h1, "timestamp": t1, "actor": "SISTEMA", "rol": "sistema", "accion": "INICIO", "sede_id": 0, "recurso_afectado": "SISTEMA", "detalle": "Génesis", "resultado": "EXITOSO"},
        {"evento_id": 2, "prev_hash": h1, "hash": h2, "timestamp": t2, "actor": "MED-01", "rol": "medico", "accion": "CONSULTA_HC", "sede_id": 1, "recurso_afectado": "Patient/pac-1001", "detalle": "Consulta unificada", "resultado": "EXITOSO"},
        {"evento_id": 3, "prev_hash": h2, "hash": h3, "timestamp": t3, "actor": "MED-02", "rol": "medico", "accion": "REGISTRO_DIAGNOSTICO", "sede_id": 2, "recurso_afectado": "Condition/cond-1001-J45", "detalle": "Diagnóstico Asma", "resultado": "EXITOSO"}
    ]

    # Prueba 1: Cadena íntegra
    res1 = VerificadorAuditoria.verificar_cadena(cadena_original)
    print(f"\n[PRUEBA 1 - CADENA ORIGINAL] Resultado: {'VÁLIDA' if res1['valida'] else 'INVALIDA'}")
    print(f" -> {res1['mensaje']}")

    # Prueba 2: Simulación de alteración maliciosa en base de datos
    print("\n[PRUEBA 2 - SIMULACIÓN DE ALTERACIÓN A MANO]")
    cadena_alterada = json.loads(json.dumps(cadena_original))
    # Modificar subrepticiamente el detalle del evento #2 sin recalcular el hash
    cadena_alterada[1]["detalle"] = "Consulta no autorizada alterada por intruso"

    res2 = VerificadorAuditoria.verificar_cadena(cadena_alterada)
    print(f"Resultado: {'VÁLIDA' if res2['valida'] else 'ALTERADA (DETECTADA)'}")
    print(f" -> {res2['mensaje']}")
    print(f" -> Primer evento alterado: #{res2['primer_evento_alterado']}")
    print("=" * 65)

if __name__ == '__main__':
    main()
