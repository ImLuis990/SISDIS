#!/usr/bin/env python3
"""
test_vistas_rbac.py — Pruebas de Control de Acceso y Aislamiento de Vistas por Rol
Verifica que las vistas web estén efectivamente separadas y protegidas:
- Usuarios no autenticados son redirigidos a /login.
- Usuarios con rol 'paciente' tienen acceso a /paciente pero reciben 403 en /medico, /admision y /auditor.
- Pacientes tienen bloqueado consultar historias de otros pacientes en la API (Habeas Data 403).
- Admisionistas tienen acceso a /admision pero reciben 403 en /medico.
- Médicos tienen acceso a /medico pero reciben 403 en /auditor.
- Cierre de sesión limpia cookies y redirige a /login.
"""

import unittest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.main import app
from app.seguridad import GestorSeguridad

class TestVistasAisladasRBAC(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app, follow_redirects=False)

    def test_01_raiz_sin_autenticacion_redirige_a_login(self):
        """Acceder a '/' sin token redirige inmediatamente a /login."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers["location"], "/login")

    def test_02_vistas_protegidas_redirigen_a_login_si_no_hay_sesion(self):
        """Intentar ingresar a /paciente, /medico, /admision o /auditor sin login redirige a /login."""
        for ruta in ["/paciente", "/medico", "/admision", "/auditor"]:
            res = self.client.get(ruta)
            self.assertEqual(res.status_code, 302, f"La ruta {ruta} debió redirigir a login")
            self.assertIn("/login", res.headers["location"])

    def test_03_paciente_accede_a_su_portal(self):
        """Un usuario con rol 'paciente' puede ver /paciente correctamente (200 OK)."""
        auth_pac = GestorSeguridad.autenticar_con_ambos_factores("1001", "paciente123", GestorSeguridad.generar_totp("JBSWY3DPEHPK3PXP"))
        token = auth_pac["token"]

        res = self.client.get("/paciente", cookies={"sisdis_token": token})
        self.assertEqual(res.status_code, 200)
        self.assertIn("Mi Historia Clínica Unificada", res.text)
        self.assertIn("Carlos Pérez", res.text)

    def test_04_paciente_bloqueado_en_vistas_medica_admision_auditoria(self):
        """Un usuario con rol 'paciente' recibe 403 Forbidden al intentar ingresar a /medico, /admision o /auditor."""
        auth_pac = GestorSeguridad.autenticar_con_ambos_factores("1001", "paciente123", GestorSeguridad.generar_totp("JBSWY3DPEHPK3PXP"))
        token = auth_pac["token"]

        for ruta in ["/medico", "/admision", "/auditor"]:
            res = self.client.get(ruta, cookies={"sisdis_token": token})
            self.assertEqual(res.status_code, 403, f"El paciente no debe acceder a {ruta} (esperado 403)")
            self.assertIn("Acceso Denegado", res.text)
            self.assertIn("PACIENTE", res.text.upper())

    def test_05_paciente_habeas_data_bloqueo_en_api(self):
        """En la API, un paciente solo consulta su documento (1001); si pide otro (1007) recibe 403."""
        auth_pac = GestorSeguridad.autenticar_con_ambos_factores("1001", "paciente123", GestorSeguridad.generar_totp("JBSWY3DPEHPK3PXP"))
        token = auth_pac["token"]

        # Su propio documento -> 200
        r_propio = self.client.get("/api/paciente/1001/historia", cookies={"sisdis_token": token})
        self.assertEqual(r_propio.status_code, 200)

        # Documento ajeno -> 403
        r_ajeno = self.client.get("/api/paciente/1007/historia", cookies={"sisdis_token": token})
        self.assertEqual(r_ajeno.status_code, 403)
        self.assertIn("Acceso denegado", r_ajeno.json().get("detail", ""))

    def test_06_admisionista_accede_a_admision_pero_no_a_medico(self):
        """Admisionista entra a /admision pero recibe 403 en /medico."""
        auth_adm = GestorSeguridad.autenticar_con_ambos_factores("admision1", "admin123", GestorSeguridad.generar_totp("MNUWE3TFOBZGS3TH"))
        token = auth_adm["token"]

        # /admision -> 200
        r_adm = self.client.get("/admision", cookies={"sisdis_token": token})
        self.assertEqual(r_adm.status_code, 200)
        self.assertIn("Admisión &amp; Triage", r_adm.text)

        # /medico -> 403
        r_med = self.client.get("/medico", cookies={"sisdis_token": token})
        self.assertEqual(r_med.status_code, 403)

    def test_07_medico_accede_a_medico_pero_no_a_auditor(self):
        """Médico accede a /medico pero recibe 403 en /auditor."""
        auth_med = GestorSeguridad.autenticar_con_ambos_factores("medico1", "medico123", GestorSeguridad.generar_totp("NB2HI4DTHIXS633P"))
        token = auth_med["token"]

        # /medico -> 200
        r_med = self.client.get("/medico", cookies={"sisdis_token": token})
        self.assertEqual(r_med.status_code, 200)
        self.assertIn("Estación Clínica Médica", r_med.text)

        # /auditor -> 403
        r_aud = self.client.get("/auditor", cookies={"sisdis_token": token})
        self.assertEqual(r_aud.status_code, 403)

    def test_08_auditor_accede_a_auditor(self):
        """Auditor tiene acceso pleno a /auditor y reportes."""
        auth_aud = GestorSeguridad.autenticar_con_ambos_factores("auditor1", "auditor123", GestorSeguridad.generar_totp("OBVWG2DBMFRGGZDF"))
        token = auth_aud["token"]

        r_aud = self.client.get("/auditor", cookies={"sisdis_token": token})
        self.assertEqual(r_aud.status_code, 200)
        self.assertIn("Auditoría Institucional", r_aud.text)

    def test_09_logout_limpia_cookie(self):
        """Cerrar sesión borra la cookie 'sisdis_token' y redirige a /login."""
        res = self.client.get("/logout", cookies={"sisdis_token": "dummy_token"})
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["location"])
        set_cookie = res.headers.get("set-cookie", "")
        self.assertIn("sisdis_token=", set_cookie)

if __name__ == '__main__':
    unittest.main()
