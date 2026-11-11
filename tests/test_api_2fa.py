#!/usr/bin/env python3
"""
test_api_2fa.py — Pruebas de Integración de Endpoints HTTP para Autenticación en Dos Pasos (2FA)
Valida los flujos de la API REST:
- POST /api/auth/login (Paso 1 y login directo)
- POST /api/auth/verificar-2fa (Paso 2 con OTP y TOTP RFC 6238)
- POST /api/auth/reenviar-2fa (Regeneración de código de desafío)
- GET /api/auth/2fa/info/{usuario} (Configuración y URI TOTP)
"""

import unittest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.main import app
from app.seguridad import GestorSeguridad

class TestAPIAutenticacion2FA(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_login_paso1_emite_desafio_2fa(self):
        """Paso 1: Credenciales válidas sin 2FA devuelven un desafío con temp_token."""
        res = self.client.post("/api/auth/login", json={"usuario": "medico1", "clave": "medico123"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("requiere_2fa"))
        self.assertEqual(data.get("usuario"), "medico1")
        self.assertEqual(data.get("rol"), "medico")
        self.assertIn("temp_token", data)
        self.assertIn("codigo_simulado", data)
        self.assertEqual(len(data["codigo_simulado"]), 6)

    def test_02_login_paso1_clave_incorrecta(self):
        """Paso 1: Contraseña incorrecta rechaza la solicitud con 401."""
        res = self.client.post("/api/auth/login", json={"usuario": "medico1", "clave": "erronea"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Credenciales incorrectas", res.json().get("detail", ""))

    def test_03_verificar_2fa_exitoso_con_otp(self):
        """Paso 2: Código OTP generado completa la autenticación y emite token JWT con 2FA verificado."""
        # Paso 1
        r1 = self.client.post("/api/auth/login", json={"usuario": "medico1", "clave": "medico123"})
        d1 = r1.json()
        temp_token = d1["temp_token"]
        otp = d1["codigo_simulado"]

        # Paso 2
        r2 = self.client.post("/api/auth/verificar-2fa", json={"temp_token": temp_token, "codigo_2fa": otp})
        self.assertEqual(r2.status_code, 200)
        d2 = r2.json()
        self.assertTrue(d2.get("mfa_verificado"))
        self.assertEqual(d2.get("rol"), "medico")
        self.assertIn("token", d2)

    def test_04_verificar_2fa_codigo_invalido(self):
        """Paso 2: Código de 6 dígitos erróneo es rechazado con 401."""
        r1 = self.client.post("/api/auth/login", json={"usuario": "medico1", "clave": "medico123"})
        d1 = r1.json()
        temp_token = d1["temp_token"]

        codigo_malo = "000000" if d1["codigo_simulado"] != "000000" else "111111"
        r2 = self.client.post("/api/auth/verificar-2fa", json={"temp_token": temp_token, "codigo_2fa": codigo_malo})
        self.assertEqual(r2.status_code, 401)

    def test_05_verificar_2fa_con_totp_rfc6238(self):
        """Paso 2: Un código TOTP generado dinámicamente mediante el secreto Base32 es aceptado."""
        r1 = self.client.post("/api/auth/login", json={"usuario": "medico1", "clave": "medico123"})
        d1 = r1.json()
        temp_token = d1["temp_token"]
        secret_b32 = d1["secret_2fa"]

        totp_code = GestorSeguridad.generar_totp(secret_b32)
        r2 = self.client.post("/api/auth/verificar-2fa", json={"temp_token": temp_token, "codigo_2fa": totp_code})
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.json().get("mfa_verificado"))

    def test_06_reenviar_codigo_2fa(self):
        """Endpoint de reenvío emite un nuevo token temporal y código OTP."""
        r1 = self.client.post("/api/auth/login", json={"usuario": "1001", "clave": "paciente123"})
        d1 = r1.json()
        t1 = d1["temp_token"]

        r_reenvio = self.client.post("/api/auth/reenviar-2fa", json={"temp_token": t1})
        self.assertEqual(r_reenvio.status_code, 200)
        d_reenvio = r_reenvio.json()
        self.assertIn("temp_token", d_reenvio)
        self.assertIn("codigo_simulado", d_reenvio)

        # Probar que el nuevo código funciona
        r_verif = self.client.post("/api/auth/verificar-2fa", json={
            "temp_token": d_reenvio["temp_token"],
            "codigo_2fa": d_reenvio["codigo_simulado"]
        })
        self.assertEqual(r_verif.status_code, 200)
        self.assertEqual(r_verif.json().get("usuario"), "1001")

    def test_07_login_directo_con_ambos_factores(self):
        """Permite autenticación directa en una sola petición cuando se suministran ambos factores."""
        totp_medico = GestorSeguridad.generar_totp("NB2HI4DTHIXS633P")
        res = self.client.post("/api/auth/login", json={
            "usuario": "medico1",
            "clave": "medico123",
            "codigo_2fa": totp_medico
        })
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertTrue(d.get("mfa_verificado"))
        self.assertIn("token", d)

    def test_08_obtener_info_2fa_usuario(self):
        """Consulta de configuración 2FA y URI para vincular con Google Authenticator."""
        res = self.client.get("/api/auth/2fa/info/medico1")
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d.get("usuario"), "medico1")
        self.assertEqual(d.get("secret_2fa"), "NB2HI4DTHIXS633P")
        self.assertIn("otpauth://totp/SISDIS:medico1", d.get("totp_uri", ""))

if __name__ == '__main__':
    unittest.main()
