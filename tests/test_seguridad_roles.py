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

    def test_06_inicio_login_2fa_emite_desafio_temporal(self):
        """Paso 1 del 2FA: Credenciales válidas emiten un token temporal de desafío y código OTP."""
        desafio = GestorSeguridad.iniciar_login_2fa("medico1", "medico123")
        self.assertIsNotNone(desafio)
        self.assertTrue(desafio["requiere_2fa"])
        self.assertEqual(desafio["usuario"], "medico1")
        self.assertEqual(desafio["rol"], "medico")
        self.assertIn("temp_token", desafio)
        self.assertIn("codigo_simulado", desafio)
        self.assertEqual(len(desafio["codigo_simulado"]), 6)
        self.assertTrue(desafio["codigo_simulado"].isdigit())

        # Validar payload del token temporal
        payload_temp = GestorSeguridad.validar_token_jwt(desafio["temp_token"])
        self.assertIsNotNone(payload_temp)
        self.assertEqual(payload_temp["tipo"], "2fa_desafio")
        self.assertEqual(payload_temp["sub"], "medico1")

    def test_07_login_2fa_codigo_correcto_emite_jwt_con_mfa(self):
        """Paso 2 del 2FA: Código OTP válido emite el token JWT definitivo con claim mfa_verificado."""
        desafio = GestorSeguridad.iniciar_login_2fa("medico1", "medico123")
        temp_token = desafio["temp_token"]
        codigo_otp = desafio["codigo_simulado"]

        valido, msg, auth = GestorSeguridad.verificar_segundo_paso_2fa(temp_token, codigo_otp)
        self.assertTrue(valido)
        self.assertIn("exitosa", msg.lower())
        self.assertIsNotNone(auth)
        self.assertEqual(auth["usuario"], "medico1")
        self.assertEqual(auth["rol"], "medico")
        self.assertTrue(auth["mfa_verificado"])
        self.assertIn("token", auth)

        # Validar token final
        final_payload = GestorSeguridad.validar_token_jwt(auth["token"])
        self.assertIsNotNone(final_payload)
        self.assertTrue(final_payload.get("mfa_verificado"))

    def test_08_login_2fa_codigo_incorrecto_es_rechazado(self):
        """Paso 2 del 2FA: Código de verificación erróneo es rechazado sin emitir token."""
        desafio = GestorSeguridad.iniciar_login_2fa("medico1", "medico123")
        temp_token = desafio["temp_token"]

        codigo_falso = "999999" if desafio["codigo_simulado"] != "999999" else "888888"
        valido, msg, auth = GestorSeguridad.verificar_segundo_paso_2fa(temp_token, codigo_falso)
        self.assertFalse(valido)
        self.assertIsNone(auth)
        self.assertIn("incorrecto", msg.lower())

    def test_09_login_2fa_totp_rfc6238_compatible(self):
        """Soporte TOTP RFC 6238 estándar: Un código generado desde la clave Base32 es aceptado."""
        sec_b32 = "NB2HI4DTHIXS633P"  # Secret de medico1
        totp_code = GestorSeguridad.generar_totp(sec_b32)
        self.assertEqual(len(totp_code), 6)
        self.assertTrue(totp_code.isdigit())

        # Validar con el verificador TOTP
        self.assertTrue(GestorSeguridad.verificar_totp(sec_b32, totp_code))

        # Probar autenticación directa con ambos factores
        auth_direct = GestorSeguridad.autenticar_con_ambos_factores("medico1", "medico123", totp_code)
        self.assertIsNotNone(auth_direct)
        self.assertEqual(auth_direct["rol"], "medico")
        self.assertTrue(auth_direct["mfa_verificado"])

    def test_10_regeneracion_codigo_2fa(self):
        """Permite regenerar y reenviar un nuevo código OTP para el desafío temporal."""
        desafio1 = GestorSeguridad.iniciar_login_2fa("1001", "paciente123")
        temp_token1 = desafio1["temp_token"]

        desafio2 = GestorSeguridad.regenerar_codigo_desafio(temp_token1)
        self.assertIsNotNone(desafio2)
        self.assertIn("temp_token", desafio2)
        self.assertIn("codigo_simulado", desafio2)
        self.assertEqual(len(desafio2["codigo_simulado"]), 6)

        # El nuevo código debe ser válido para el nuevo temp_token
        valido, _, auth = GestorSeguridad.verificar_segundo_paso_2fa(desafio2["temp_token"], desafio2["codigo_simulado"])
        self.assertTrue(valido)
        self.assertEqual(auth["usuario"], "1001")

    def test_11_verificacion_acceso_con_exigencia_2fa(self):
        """Endpoints críticos pueden exigir que el token tenga 2FA verificado obligatoriamente."""
        # Token con 2FA completado
        auth_con_2fa = GestorSeguridad.autenticar_con_ambos_factores("medico1", "medico123", GestorSeguridad.generar_totp("NB2HI4DTHIXS633P"))
        ok, _, _ = GestorSeguridad.verificar_acceso(auth_con_2fa["token"], roles_permitidos=["medico"], exigir_2fa=True)
        self.assertTrue(ok)

        # Token sin 2FA completado (login simple histórico)
        auth_sin_2fa = GestorSeguridad.autenticar_usuario("medico1", "medico123")
        ok_sin, motivo, _ = GestorSeguridad.verificar_acceso(auth_sin_2fa["token"], roles_permitidos=["medico"], exigir_2fa=True)
        self.assertFalse(ok_sin)
        self.assertIn("2FA", motivo)

if __name__ == '__main__':
    unittest.main()
