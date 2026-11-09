#!/usr/bin/env python3
"""
test_normalizador_fhir.py — Pruebas Unitarias del Normalizador FHIR R4
Valida la generación de recursos Patient, Encounter, Condition y Observation,
el empaquetado determinista en Bundle tipo transaction y el rechazo de datos inválidos.
"""

import unittest
import sys
import os

# Asegurar importación de fhir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fhir.normalizador import NormalizadorFHIR, NormalizadorError

class TestNormalizadorFHIR(unittest.TestCase):

    def test_01_crear_paciente_valido(self):
        """Caso 1: Paciente válido con nombre formateado y fecha de nacimiento."""
        paciente = NormalizadorFHIR.crear_recurso_patient(
            documento="1007",
            nombre_completo="Rojas^Andrea",
            sexo="F",
            fecha_nacimiento="19900214"
        )
        self.assertEqual(paciente["resourceType"], "Patient")
        self.assertEqual(paciente["id"], "pac-1007")
        self.assertEqual(paciente["gender"], "female")
        self.assertEqual(paciente["birthDate"], "1990-02-14")
        self.assertEqual(paciente["name"][0]["family"], "Rojas")
        self.assertEqual(paciente["name"][0]["given"], ["Andrea"])
        self.assertEqual(paciente["identifier"][0]["value"], "1007")

    def test_02_crear_encounter_valido(self):
        """Caso 2: Encuentro asistencial con triage, modalidad y profesional."""
        encounter = NormalizadorFHIR.crear_recurso_encounter(
            encounter_id="V-S2-0101",
            patient_id="pac-1007",
            clase="O", # Ambulatorio
            fecha_ingreso="20261107101500",
            sede_nombre="Sede 2 Cartagena",
            profesional="MED-02^Ruiz^Mateo",
            triage="2"
        )
        self.assertEqual(encounter["resourceType"], "Encounter")
        self.assertEqual(encounter["id"], "enc-V-S2-0101")
        self.assertEqual(encounter["status"], "finished")
        self.assertEqual(encounter["class"]["code"], "AMB")
        self.assertEqual(encounter["subject"]["reference"], "Patient/pac-1007")
        self.assertEqual(encounter["period"]["start"], "2026-11-07T10:15:00Z")
        self.assertEqual(encounter["priority"]["coding"][0]["code"], "2")
        self.assertIn("Mateo", encounter["participant"][0]["individual"]["display"])

    def test_03_crear_condition_cie10(self):
        """Caso 3: Condición diagnóstica con terminología estándar CIE-10."""
        condition = NormalizadorFHIR.crear_recurso_condition(
            condition_id="1007-J45.9",
            patient_id="pac-1007",
            encounter_id="enc-V-S2-0101",
            cie10="J45.9",
            descripcion="Asma",
            fecha="20261107"
        )
        self.assertEqual(condition["resourceType"], "Condition")
        self.assertEqual(condition["id"], "cond-1007-J45-9")
        self.assertEqual(condition["clinicalStatus"]["coding"][0]["code"], "active")
        self.assertEqual(condition["verificationStatus"]["coding"][0]["code"], "confirmed")
        self.assertEqual(condition["code"]["coding"][0]["code"], "J45.9")
        self.assertEqual(condition["code"]["coding"][0]["system"], "http://hl7.org/fhir/sid/icd-10")
        self.assertEqual(condition["subject"]["reference"], "Patient/pac-1007")
        self.assertEqual(condition["encounter"]["reference"], "Encounter/enc-V-S2-0101")

    def test_04_crear_observation_loinc(self):
        """Caso 4: Observación clínica de laboratorio con código estándar LOINC."""
        obs = NormalizadorFHIR.crear_recurso_observation(
            obs_id="1001-718-7",
            patient_id="pac-1001",
            encounter_id="enc-V-S1-0150",
            loinc_code="718-7",
            descripcion="Hemoglobina",
            valor="13.8",
            unidad="g/dL",
            fecha="202611071100"
        )
        self.assertEqual(obs["resourceType"], "Observation")
        self.assertEqual(obs["id"], "obs-1001-718-7")
        self.assertEqual(obs["code"]["coding"][0]["code"], "718-7")
        self.assertEqual(obs["code"]["coding"][0]["system"], "http://loinc.org")
        self.assertEqual(obs["valueQuantity"]["value"], 13.8)
        self.assertEqual(obs["valueQuantity"]["unit"], "g/dL")
        self.assertEqual(obs["subject"]["reference"], "Patient/pac-1001")

    def test_05_bundle_transaction_idempotente(self):
        """Caso 5: Empaquetado en Bundle transaction con método PUT determinista."""
        pac = NormalizadorFHIR.crear_recurso_patient("1007", "Rojas^Andrea", "F")
        enc = NormalizadorFHIR.crear_recurso_encounter("V-01", pac["id"], "O")
        cond = NormalizadorFHIR.crear_recurso_condition("c1", pac["id"], enc["id"], "J45.9", "Asma")

        bundle = NormalizadorFHIR.empaquetar_en_bundle([pac, enc, cond])
        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "transaction")
        self.assertEqual(len(bundle["entry"]), 3)

        # Verificar método PUT determinista en cada entrada
        for entry in bundle["entry"]:
            req = entry["request"]
            self.assertEqual(req["method"], "PUT")
            res_type = entry["resource"]["resourceType"]
            res_id = entry["resource"]["id"]
            self.assertEqual(req["url"], f"{res_type}/{res_id}")

    def test_06_validacion_rechazo_datos_invalidos(self):
        """Caso 6: Detección estricta de múltiples motivos de rechazo en mensaje inválido."""
        # Documento no numérico ('ABC123'), Sexo inválido ('X'), Nombre vacío
        motivos = NormalizadorFHIR.validar_datos_paciente(
            documento="ABC123",
            nombre="",
            sexo="X"
        )
        self.assertGreaterEqual(len(motivos), 3)
        self.assertTrue(any("Documento no numérico" in m for m in motivos))
        self.assertTrue(any("Nombre" in m for m in motivos))
        self.assertTrue(any("Sexo no válido" in m for m in motivos))

    def test_07_validacion_documento_demasiado_corto(self):
        """Caso 7: Detección de documento con menos de 4 dígitos."""
        motivos = NormalizadorFHIR.validar_datos_paciente(
            documento="12",
            nombre="Nombre Corto",
            sexo="M"
        )
        self.assertTrue(any("longitud inválida" in m for m in motivos))

if __name__ == '__main__':
    unittest.main()
