#!/usr/bin/env python3
"""
test_hsb_mensajes.py — Pruebas de Integración de Mensajería del HSB
Verifica el procesamiento de los archivos de ejemplo oficiales:
- 01_adt_a01_valido_sede2.hl7 -> Entregado (Patient 1007, J45.9, Sede 2)
- 02_oru_r01_laboratorio_sede1.hl7 -> Entregado (Observation 718-7 = 13.8 g/dL, Sede 1)
- 03_adt_a01_invalido.hl7 -> Rechazado con 3 motivos
- 04_sede3_legado.csv -> 3 entregados y 2 rechazados
- Idempotencia: Reenvío devuelve 'duplicado' sin crear duplicados
- Cola de reintentos y Dead-Letter Queue (DLQ)
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from hsb.service import HSBService

EJEMPLOS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ejemplos'))

class TestHSBMensajeria(unittest.TestCase):

    def setUp(self):
        csv_terminologia = os.path.join(EJEMPLOS_DIR, '05_ref_terminologia.csv')
        # Inicializamos HSB mockeando la URL de FHIR para pruebas locales autónomas
        self.hsb = HSBService(hapi_fhir_url="http://mock-hapi:8080/fhir", ref_csv_path=csv_terminologia)
        # Mock de envío exitoso a HAPI para pruebas en memoria
        self.hsb._enviar_a_hapi_con_reintentos = lambda bundle, idemp, max_intentos=4: (True, "Mock HAPI OK")

    def test_01_adt_a01_valido_sede2(self):
        """01_adt_a01_valido_sede2.hl7: Debe ser entregado (Patient 1007, Encounter y Condition J45.9 en sede 2)."""
        ruta = os.path.join(EJEMPLOS_DIR, '01_adt_a01_valido_sede2.hl7')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()

        codigo, res = self.hsb.procesar_mensaje_hl7(contenido)
        self.assertEqual(codigo, 200)
        self.assertEqual(res["status"], "entregado")
        self.assertEqual(res["paciente"], "1007")
        self.assertEqual(res["sede"], 2)
        self.assertIn("audit_hash", res)
        self.assertGreaterEqual(res["recursos_creados"], 3) # Patient, Encounter, Condition

    def test_02_oru_r01_laboratorio_sede1(self):
        """02_oru_r01_laboratorio_sede1.hl7: Debe ser entregado (Observation 718-7 = 13.8 g/dL para 1001 en sede 1)."""
        ruta = os.path.join(EJEMPLOS_DIR, '02_oru_r01_laboratorio_sede1.hl7')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()

        codigo, res = self.hsb.procesar_mensaje_hl7(contenido)
        self.assertEqual(codigo, 200)
        self.assertEqual(res["status"], "entregado")
        self.assertEqual(res["paciente"], "1001")
        self.assertEqual(res["sede"], 1)

        # Verificar presencia de la observación
        bundle = res.get("bundle", {})
        recursos = [e["resource"] for e in bundle.get("entry", [])]
        obs = next((r for r in recursos if r["resourceType"] == "Observation"), None)
        self.assertIsNotNone(obs)
        self.assertEqual(obs["code"]["coding"][0]["code"], "718-7")
        self.assertEqual(obs["valueQuantity"]["value"], 13.8)
        self.assertEqual(obs["valueQuantity"]["unit"], "g/dL")

    def test_03_adt_a01_invalido_tres_motivos(self):
        """03_adt_a01_invalido.hl7: Debe ser rechazado con 3 motivos (doc no numérico, sexo no válido, dx sin mapeo)."""
        ruta = os.path.join(EJEMPLOS_DIR, '03_adt_a01_invalido.hl7')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()

        codigo, res = self.hsb.procesar_mensaje_hl7(contenido)
        self.assertEqual(codigo, 400)
        self.assertEqual(res["status"], "rechazado")
        motivos = res.get("motivos", [])

        self.assertGreaterEqual(len(motivos), 3, f"Se esperaban al menos 3 motivos, se obtuvieron: {motivos}")
        self.assertTrue(any("Documento no numérico" in m for m in motivos))
        self.assertTrue(any("Sexo no válido" in m for m in motivos))
        self.assertTrue(any("sin mapeo" in m for m in motivos))

    def test_04_sede3_legado_csv(self):
        """04_sede3_legado.csv: 3 entregados (1008, 1009, 1010) y 2 rechazados (1011 por dx sin mapeo, 12 por doc corto)."""
        ruta = os.path.join(EJEMPLOS_DIR, '04_sede3_legado.csv')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()

        res = self.hsb.procesar_archivo_csv(contenido, sede_id=3)
        self.assertEqual(res["total_procesados"], 5)
        self.assertEqual(res["total_entregados"], 3)
        self.assertEqual(res["total_rechazados"], 2)

        docs_entregados = [e["documento"] for e in res["entregados"]]
        self.assertIn("1008", docs_entregados)
        self.assertIn("1009", docs_entregados)
        self.assertIn("1010", docs_entregados)

        docs_rechazados = [r["documento"] for r in res["rechazados"]]
        self.assertIn("1011", docs_rechazados) # DOLOR MISTERIOSO sin mapeo
        self.assertIn("12", docs_rechazados)   # Documento corto (2 dígitos)

    def test_05_idempotencia_duplicado(self):
        """Reenviar el mensaje 01 dos veces: la segunda responde 'duplicado' y no duplica."""
        ruta = os.path.join(EJEMPLOS_DIR, '01_adt_a01_valido_sede2.hl7')
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()

        # Primer envío -> entregado
        c1, r1 = self.hsb.procesar_mensaje_hl7(contenido)
        self.assertEqual(r1["status"], "entregado")

        # Segundo envío -> duplicado
        c2, r2 = self.hsb.procesar_mensaje_hl7(contenido)
        self.assertEqual(c2, 200)
        self.assertEqual(r2["status"], "duplicado")
        self.assertIn("Idempotencia", r2["mensaje"])

    def test_06_dead_letter_queue_por_fallo(self):
        """Simulación de caída persistente: supera 4 reintentos y pasa a Dead-Letter Queue (muerto)."""
        # HSB con envío forzado a fallar
        hsb_fallo = HSBService()
        hsb_fallo._enviar_a_hapi_con_reintentos = lambda b, idemp, max_i=4: (False, "Fallo simulado HAPI apagado")

        hl7_test = "MSH|^~\\&|HIS_SEDE2|SEDE2|HSB|CENTRAL|20261107||ADT^A01|MSG-9999|P|2.5\rPID|1||9090^^^HIS||Gomez^Juan||19950101|M\rPV1|1|O|||||MED-01||||||||||||V-S2-9090|||||||||||||||||||||||||202611071000\rDG1|1||J45.9^Asma^I10||20261107|A"
        cod, res = hsb_fallo.procesar_mensaje_hl7(hl7_test)
        self.assertEqual(cod, 503)
        self.assertEqual(res["status"], "muerto")

if __name__ == '__main__':
    unittest.main()
