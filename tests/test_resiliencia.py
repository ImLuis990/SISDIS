#!/usr/bin/env python3
"""
test_resiliencia.py — Pruebas de Resiliencia y Tolerancia a Fallos Parciales
Verifica que cuando un nodo de sede se apaga (docker stop pg_sede2),
la vista unificada continúa respondiendo con los otros nodos y marca la sede como no disponible.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.consulta_unificada import MotorConsultaUnificada

class TestResiliencia(unittest.TestCase):

    def setUp(self):
        self.motor = MotorConsultaUnificada()

    def test_01_consulta_unificada_tres_sedes_activas(self):
        """Con las 3 sedes activas, la historia del paciente 1001 consolida atenciones de Sincelejo, Cartagena y Corozal."""
        res = self.motor.consultar_historia_unificada(1001)
        self.assertEqual(res["estado_red"], "completo")
        self.assertIsNone(res["alerta"])
        self.assertEqual(res["total_atenciones"], 3) # 1 de Sede 1, 1 de Sede 2, 1 de Sede 3

        sedes = res["sedes"]
        self.assertTrue(sedes["sede_1"]["disponible"])
        self.assertTrue(sedes["sede_2"]["disponible"])
        self.assertTrue(sedes["sede_3"]["disponible"])

    def test_02_tolerancia_a_caida_de_sede_cartagena(self):
        """Si la Sede 2 Cartagena cae (docker stop pg_sede2), el sistema responde en modo degradado con 2 sedes."""
        # Simular caída de Sede 2
        self.motor.simular_caida_sede(2)

        res = self.motor.consultar_historia_unificada(1001)

        # 1. El sistema no colapsa: sigue respondiendo con datos de Sede 1 y Sede 3
        self.assertEqual(res["estado_red"], "degradado")
        self.assertIsNotNone(res["alerta"])
        self.assertIn("degradado", res["alerta"])

        # 2. Las atenciones de Sede 1 y Sede 3 siguen presentes (2 atenciones)
        self.assertEqual(res["total_atenciones"], 2)

        # 3. La Sede 2 está claramente marcada como no disponible
        sedes = res["sedes"]
        self.assertTrue(sedes["sede_1"]["disponible"])
        self.assertFalse(sedes["sede_2"]["disponible"])
        self.assertEqual(sedes["sede_2"]["estado"], "no_disponible (degradado)")
        self.assertTrue(sedes["sede_3"]["disponible"])

    def test_03_recuperacion_automatica_al_volver_sede(self):
        """Al reactivarse la Sede 2 (docker start pg_sede2), la red recupera el estado completo al 100%."""
        self.motor.simular_caida_sede(2)
        # Sede vuelve a encender
        self.motor.restaurar_sede(2)

        res = self.motor.consultar_historia_unificada(1001)
        self.assertEqual(res["estado_red"], "completo")
        self.assertEqual(res["total_atenciones"], 3)
        self.assertTrue(res["sedes"]["sede_2"]["disponible"])

if __name__ == '__main__':
    unittest.main()
