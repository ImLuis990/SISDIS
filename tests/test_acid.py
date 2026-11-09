#!/usr/bin/env python3
"""
test_acid.py — Pruebas Automatizadas de Atomicidad (ACID)
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.demo_acid import DemostradorACID

class TestAtomicidadACID(unittest.TestCase):

    def setUp(self):
        self.demo = DemostradorACID(":memory:")

    def test_transaccion_exitosa_commit(self):
        """Verifica que una transacción sin fallas persiste tanto usuario como atención."""
        doc = 1007
        res = self.demo.registrar_atencion_atomica(
            documento_id=doc,
            nombre="Andrea Rojas",
            sexo="F",
            entidad="Sede 2 Cartagena",
            triage="2",
            forzar_error=False
        )
        self.assertTrue(res["exito"])
        self.assertEqual(res["accion"], "COMMIT_EXITOSO")

        n_user, n_aten = self.demo.contar_registros(doc)
        self.assertEqual(n_user, 1)
        self.assertEqual(n_aten, 1)

    def test_transaccion_con_error_rollback(self):
        """Verifica que ante un fallo a mitad de transacción se ejecuta ROLLBACK sin dejar residuos."""
        doc = 888888
        # Comprobar que no existe antes
        n_user_init, n_aten_init = self.demo.contar_registros(doc)
        self.assertEqual(n_user_init, 0)
        self.assertEqual(n_aten_init, 0)

        # Disparar transacción fallida
        res = self.demo.registrar_atencion_atomica(
            documento_id=doc,
            nombre="Paciente Fallido",
            sexo="M",
            entidad="Sede 1 Sincelejo",
            triage="3",
            forzar_error=True
        )
        self.assertFalse(res["exito"])
        self.assertEqual(res["accion"], "ROLLBACK_EJECUTADO")
        self.assertIn("ERROR_FORZADO", res["error"])

        # Comprobar que NINGÚN registro quedó guardado
        n_user_after, n_aten_after = self.demo.contar_registros(doc)
        self.assertEqual(n_user_after, 0, "El usuario no debió guardarse tras el rollback")
        self.assertEqual(n_aten_after, 0, "La atención no debió guardarse tras el rollback")

if __name__ == '__main__':
    unittest.main()
