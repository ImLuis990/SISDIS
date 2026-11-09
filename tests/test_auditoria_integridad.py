#!/usr/bin/env python3
"""
test_auditoria_integridad.py — Pruebas Automatizadas de Auditoría Encadenada
Verifica que la cadena inmutable detecte cualquier alteración o manipulación de datos.
"""

import unittest
import hashlib
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.verificador_auditoria import VerificadorAuditoria

class TestAuditoriaIntegridad(unittest.TestCase):

    def setUp(self):
        # Crear cadena criptográfica válida
        genesis_hash = "0" * 64
        t1 = "2026-11-09T10:00:00Z"
        h1 = hashlib.sha256(f"{genesis_hash}_{t1}_GENESIS".encode()).hexdigest()

        t2 = "2026-11-09T10:05:00Z"
        p2 = f"{h1}|2|{t2}|1001|paciente|CONSULTA_PROPIA|1|Patient/pac-1001|Consulta de historia|EXITOSO"
        h2 = hashlib.sha256(p2.encode()).hexdigest()

        t3 = "2026-11-09T10:10:00Z"
        p3 = f"{h2}|3|{t3}|MED-01|medico|REGISTRO_DIAGNOSTICO|1|Condition/cond-1001-A09|Dx Diarrea|EXITOSO"
        h3 = hashlib.sha256(p3.encode()).hexdigest()

        self.eventos_validos = [
            {"evento_id": 1, "prev_hash": genesis_hash, "hash": h1, "timestamp": t1, "actor": "SISTEMA", "rol": "sistema", "accion": "GENESIS", "sede_id": 0, "recurso_afectado": "SISTEMA", "detalle": "Bloque génesis", "resultado": "EXITOSO"},
            {"evento_id": 2, "prev_hash": h1, "hash": h2, "timestamp": t2, "actor": "1001", "rol": "paciente", "accion": "CONSULTA_PROPIA", "sede_id": 1, "recurso_afectado": "Patient/pac-1001", "detalle": "Consulta de historia", "resultado": "EXITOSO"},
            {"evento_id": 3, "prev_hash": h2, "hash": h3, "timestamp": t3, "actor": "MED-01", "rol": "medico", "accion": "REGISTRO_DIAGNOSTICO", "sede_id": 1, "recurso_afectado": "Condition/cond-1001-A09", "detalle": "Dx Diarrea", "resultado": "EXITOSO"}
        ]

    def test_cadena_original_es_valida(self):
        """La cadena sin alteraciones supera la verificación al 100%."""
        res = VerificadorAuditoria.verificar_cadena(self.eventos_validos)
        self.assertTrue(res["valida"])
        self.assertIsNone(res["primer_evento_alterado"])
        self.assertEqual(res["total_eventos"], 3)

    def test_deteccion_de_alteracion_en_evento(self):
        """Modificar un solo carácter en la base de datos es detectado inmediatamente."""
        cadena_falsificada = json.loads(json.dumps(self.eventos_validos))
        # Alterar detalle en evento 2
        cadena_falsificada[1]["detalle"] = "Detalle falsificado por intruso"

        res = VerificadorAuditoria.verificar_cadena(cadena_falsificada)
        self.assertFalse(res["valida"])
        self.assertEqual(res["primer_evento_alterado"], 2)
        self.assertIn("ALERTA DE SEGURIDAD", res["mensaje"])

    def test_deteccion_de_rotura_de_enlace(self):
        """Eliminar un evento intermedio rompe el enlace criptográfico del siguiente."""
        # Se elimina el evento 2 y se une evento 1 directo a evento 3 sin actualizar prev_hash
        cadena_incompleta = [self.eventos_validos[0], self.eventos_validos[2]]

        res = VerificadorAuditoria.verificar_cadena(cadena_incompleta)
        self.assertFalse(res["valida"])
        self.assertIn("Enlace roto", res["mensaje"])

if __name__ == '__main__':
    unittest.main()
