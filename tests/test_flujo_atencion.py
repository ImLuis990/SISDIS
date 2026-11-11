#!/usr/bin/env python3
"""
test_flujo_atencion.py — Pruebas del Flujo Completo de Atención Clínica y Admisión
Verifica que:
- Registrar una atención médica persiste en la historia clínica unificada.
- Admitir un paciente nuevo lo registra en datos simulados y en HSB.
- Los mensajes de admisión y atención aparecen en /hsb/mensajes.
- Consultar la historia después de registrar una atención muestra la nueva atención.
"""

import unittest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.main import app, motor_consulta, hsb_service


class TestFlujoAtencionClinica(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_registrar_atencion_medica_aparece_en_historia(self):
        """Registrar una atención clínica y verificar que aparece en la historia unificada."""
        doc_nuevo = 9999
        sede = 1

        # Registrar atención médica para paciente nuevo
        resp = self.client.post("/api/medico/atencion", json={
            "documento_id": doc_nuevo,
            "sede_id": sede,
            "cie10": "J45.9",
            "dx_desc": "Asma no especificada",
            "tecnologia": "Espirometría",
            "egreso": "Domicilio"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "registrado")
        self.assertIn("sello_integridad", data)

        # Consultar historia unificada — la atención debe existir
        resp2 = self.client.get(f"/api/paciente/{doc_nuevo}/historia")
        self.assertEqual(resp2.status_code, 200)
        historia = resp2.json()
        self.assertEqual(historia["documento_id"], doc_nuevo)
        self.assertGreaterEqual(historia["total_atenciones"], 1)

        # Verificar que la atención tiene el diagnóstico correcto
        atencion = historia["atenciones"][0]
        self.assertEqual(atencion["sede_id"], sede)
        self.assertTrue(any(d["cie10"] == "J45.9" for d in atencion.get("diagnosticos", [])))

        # Limpiar
        if doc_nuevo in motor_consulta.datos_simulados_locales.get(sede, {}):
            del motor_consulta.datos_simulados_locales[sede][doc_nuevo]

    def test_02_admitir_paciente_nuevo_aparece_en_busqueda(self):
        """Admitir un paciente nuevo y verificar que aparece en búsqueda de sedes."""
        doc_nuevo = 8888

        # Verificar que no existe antes
        resp = self.client.get(f"/api/admision/buscar/{doc_nuevo}")
        data = resp.json()
        self.assertFalse(any(s["existe"] for s in data["sedes"]))

        # Admitir paciente
        resp2 = self.client.post("/api/admision/admitir", json={
            "documento_id": doc_nuevo,
            "sede_id": 2,
            "triage": "3",
            "motivo": "Dolor abdominal"
        })
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["status"], "admitido")

        # Verificar que ahora aparece en búsqueda
        resp3 = self.client.get(f"/api/admision/buscar/{doc_nuevo}")
        data3 = resp3.json()
        sede2 = next(s for s in data3["sedes"] if s["sede_id"] == 2)
        self.assertTrue(sede2["existe"])

        # Limpiar
        if doc_nuevo in motor_consulta.datos_simulados_locales.get(2, {}):
            del motor_consulta.datos_simulados_locales[2][doc_nuevo]

    def test_03_admision_genera_mensaje_hsb(self):
        """Admitir un paciente genera un mensaje visible en /hsb/mensajes."""
        doc_nuevo = 7777
        mensajes_antes = len(hsb_service.mensajes_db)

        self.client.post("/api/admision/admitir", json={
            "documento_id": doc_nuevo,
            "sede_id": 1,
            "triage": "2",
            "motivo": "Urgencia respiratoria"
        })

        # Verificar que hay un mensaje nuevo en HSB
        resp = self.client.get("/hsb/mensajes")
        data = resp.json()
        self.assertGreater(data["total"], mensajes_antes)

        # Verificar que el mensaje tiene los campos esperados
        msg_admision = [m for m in data["mensajes"] if str(doc_nuevo) in str(m.get("documento", "")) or str(doc_nuevo) in str(m.get("paciente", ""))]
        self.assertGreaterEqual(len(msg_admision), 1)
        msg = msg_admision[0]
        self.assertEqual(msg["formato"], "ADM")
        self.assertEqual(msg["estado"], "admitido")
        self.assertEqual(msg["status"], "admitido")

        # Limpiar
        for k in list(hsb_service.mensajes_db.keys()):
            if str(doc_nuevo) in k:
                del hsb_service.mensajes_db[k]
        if doc_nuevo in motor_consulta.datos_simulados_locales.get(1, {}):
            del motor_consulta.datos_simulados_locales[1][doc_nuevo]

    def test_04_atencion_medica_genera_mensaje_hsb(self):
        """Registrar una atención médica genera un mensaje visible en /hsb/mensajes."""
        doc_nuevo = 6666
        mensajes_antes = len(hsb_service.mensajes_db)

        self.client.post("/api/medico/atencion", json={
            "documento_id": doc_nuevo,
            "sede_id": 3,
            "cie10": "I10",
            "dx_desc": "Hipertensión esencial",
            "tecnologia": "Control de presión arterial",
            "egreso": "Domicilio"
        })

        resp = self.client.get("/hsb/mensajes")
        data = resp.json()
        self.assertGreater(data["total"], mensajes_antes)

        msg_med = [m for m in data["mensajes"] if str(doc_nuevo) in str(m.get("documento", ""))]
        self.assertGreaterEqual(len(msg_med), 1)
        self.assertEqual(msg_med[0]["formato"], "MED")
        self.assertEqual(msg_med[0]["estado"], "registrado")

        # Limpiar
        for k in list(hsb_service.mensajes_db.keys()):
            if str(doc_nuevo) in k:
                del hsb_service.mensajes_db[k]
        if doc_nuevo in motor_consulta.datos_simulados_locales.get(3, {}):
            del motor_consulta.datos_simulados_locales[3][doc_nuevo]

    def test_05_paciente_admitido_tiene_historia_consultable(self):
        """Un paciente recién admitido puede ser consultado en la historia clínica."""
        doc_nuevo = 5555

        # Admitir
        self.client.post("/api/admision/admitir", json={
            "documento_id": doc_nuevo,
            "sede_id": 1,
            "triage": "4",
            "motivo": "Consulta general"
        })

        # Consultar historia
        resp = self.client.get(f"/api/paciente/{doc_nuevo}/historia")
        self.assertEqual(resp.status_code, 200)
        historia = resp.json()
        self.assertEqual(historia["documento_id"], doc_nuevo)
        self.assertGreaterEqual(historia["total_atenciones"], 1)
        self.assertEqual(historia["atenciones"][0]["triage"], "4")

        # Limpiar
        if doc_nuevo in motor_consulta.datos_simulados_locales.get(1, {}):
            del motor_consulta.datos_simulados_locales[1][doc_nuevo]
        for k in list(hsb_service.mensajes_db.keys()):
            if str(doc_nuevo) in k:
                del hsb_service.mensajes_db[k]


if __name__ == "__main__":
    unittest.main(verbosity=2)
