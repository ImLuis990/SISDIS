#!/usr/bin/env python3
"""
test_seguridad_roles.py — Pruebas de Autenticación JWT y Control de Acceso (RBAC)
Verifica que cada rol respete sus permisos y que se bloquee el acceso no autorizado (403/401).
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.seguridad import GestorSeguridad

class TestSeguridadRBAC(unittest.TestCase):

    def test_01_login_exitoso_y_token_valido(self):
        """Autenticación válida emite token JWT legítimo y verificable."""
        auth_medico = GestorSeguridad.autenticar_usuario("medico1", "medico123")
        self.assertIsNotNone(auth_medico)
        self.assertEqual(auth_medico["rol"], "medico")
        self.assertIn("token", auth_medico)

        # Validar token
        payload = GestorSeguridad.validar_token_jwt(auth_medico["token"])
        self.assertIsNotNone(payload)
        self.assertEqual(payload["rol"], "medico")
        self.assertEqual(payload["sub"], "medico1")

    def test_02_login_clave_invalida(self):
        """Credencial errónea es rechazada sin emitir token."""
        auth_fallido = GestorSeguridad.autenticar_usuario("medico1", "clave_incorrecta")
        self.assertIsNone(auth_fallido)

    def test_03_acceso_permitido_por_rol(self):
        """Médico tiene permiso para registrar diagnóstico CIE-10."""
        auth = GestorSeguridad.autenticar_usuario("medico1", "medico123")
        token = auth["token"]

        permitido, motivo, _ = GestorSeguridad.verificar_acceso(token, roles_permitidos=["medico"])
        self.assertTrue(permitido)
        self.assertEqual(motivo, "Acceso concedido")

    def test_04_acceso_denegado_admisionista_en_clinica(self):
        """Admisionista NO tiene permiso para registrar diagnósticos clínicos (403)."""
        auth_adm = GestorSeguridad.autenticar_usuario("admision1", "admin123")
        token_adm = auth_adm["token"]

        permitido, motivo, _ = GestorSeguridad.verificar_acceso(token_adm, roles_permitidos=["medico"])
        self.assertFalse(permitido)
        self.assertIn("Acceso denegado", motivo)
        self.assertIn("403", motivo)

    def test_05_confidencialidad_paciente_habeas_data(self):
        """Paciente solo puede ver su propia historia; cambiar documento en URL se bloquea (403)."""
        auth_pac = GestorSeguridad.autenticar_usuario("1001", "paciente123")
        token_pac = auth_pac["token"]

        # 1. Consulta su propio documento 1001 -> PERMITIDO
        p1, _, _ = GestorSeguridad.verificar_acceso(token_pac, roles_permitidos=["paciente"], documento_solicitado=1001)
        self.assertTrue(p1, "El paciente debe poder ver su propia historia clínica")

        # 2. Intenta consultar el documento 1007 de otro paciente -> DENEGADO (Habeas Data)
        p2, motivo2, _ = GestorSeguridad.verificar_acceso(token_pac, roles_permitidos=["paciente"], documento_solicitado=1007)
        self.assertFalse(p2, "El paciente NO debe poder acceder a datos de otro paciente")
        self.assertIn("Acceso denegado", motivo2)
        self.assertIn("403", motivo2)

if __name__ == '__main__':
    unittest.main()
