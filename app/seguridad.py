#!/usr/bin/env python3
"""
seguridad.py — Autenticación JWT, Control de Acceso Basado en Roles (RBAC) y 2FA
Maneja emisión y validación de tokens JWT firmados, autenticación en dos pasos (2FA / TOTP RFC 6238),
y control de permisos para los 4 roles del sistema clínico:
- paciente: solo accede a su propia historia clínica y auditoría de accesos.
- admisionista: busca pacientes, admite con triage, ve estado del bus (sin datos clínicos).
- medico: consulta HC completa, registra diagnósticos CIE-10, órdenes y egreso clínico.
- auditor: consulta reportes, métricas globales y verifica integridad de la auditoría.
"""

from typing import Optional, Dict, Any, List, Tuple
import datetime
import hashlib
import hmac
import base64
import json
import os
import secrets
import struct
import time

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "sisdis_super_secret_jwt_key_2026_salud_interoperable")
ALGORITHM = "HS256"
EXPIRATION_HOURS = 8
EXPIRATION_2FA_MINUTES = 5

# Base de usuarios y credenciales de prueba preconfiguradas con soporte 2FA
USUARIOS_SISTEMA: Dict[str, Dict[str, Any]] = {
    "1001": {
        "usuario": "1001",
        "clave_hash": hashlib.sha256("paciente123".encode()).hexdigest(),
        "nombre": "Carlos Pérez",
        "rol": "paciente",
        "documento_id": 1001,
        "telefono": "+57 300 555 1001",
        "email": "carlos.perez@salud.gov.co",
        "secret_2fa": "JBSWY3DPEHPK3PXP",
        "mfa_habilitado": True
    },
    "1007": {
        "usuario": "1007",
        "clave_hash": hashlib.sha256("paciente123".encode()).hexdigest(),
        "nombre": "Andrea Rojas",
        "rol": "paciente",
        "documento_id": 1007,
        "telefono": "+57 301 555 1007",
        "email": "andrea.rojas@salud.gov.co",
        "secret_2fa": "KREECTCEIVJVIUZT",
        "mfa_habilitado": True
    },
    "admision1": {
        "usuario": "admision1",
        "clave_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "nombre": "Marta Gómez (Admisión)",
        "rol": "admisionista",
        "documento_id": None,
        "telefono": "+57 302 555 2001",
        "email": "marta.gomez@salud.gov.co",
        "secret_2fa": "MNUWE3TFOBZGS3TH",
        "mfa_habilitado": True
    },
    "medico1": {
        "usuario": "medico1",
        "clave_hash": hashlib.sha256("medico123".encode()).hexdigest(),
        "nombre": "Dra. Laura Vega",
        "rol": "medico",
        "profesional_id": "MED-01",
        "documento_id": None,
        "telefono": "+57 315 555 3001",
        "email": "laura.vega@salud.gov.co",
        "secret_2fa": "NB2HI4DTHIXS633P",
        "mfa_habilitado": True
    },
    "auditor1": {
        "usuario": "auditor1",
        "clave_hash": hashlib.sha256("auditor123".encode()).hexdigest(),
        "nombre": "Lic. Roberto Blanco (Auditor)",
        "rol": "auditor",
        "documento_id": None,
        "telefono": "+57 310 555 4001",
        "email": "roberto.blanco@salud.gov.co",
        "secret_2fa": "OBVWG2DBMFRGGZDF",
        "mfa_habilitado": True
    }
}

class GestorSeguridad:
    """Manejo de tokens JWT, algoritmos 2FA (TOTP/OTP) y validaciones criptográficas sin dependencias externas pesadas."""

    @classmethod
    def _b64_url_encode(cls, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

    @classmethod
    def _b64_url_decode(cls, s: str) -> bytes:
        padding = 4 - (len(s) % 4)
        if padding != 4:
            s += '=' * padding
        return base64.urlsafe_b64decode(s.encode('utf-8'))

    @classmethod
    def crear_token_jwt(cls, payload: Dict[str, Any], secret: str = SECRET_KEY, horas_exp: Optional[int] = EXPIRATION_HOURS) -> str:
        """Emite un token JWT firmado con HMAC-SHA256."""
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = cls._b64_url_encode(json.dumps(header).encode('utf-8'))

        payload_copy = dict(payload)
        if "exp" not in payload_copy:
            horas = horas_exp if horas_exp is not None else EXPIRATION_HOURS
            exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=horas)).timestamp())
            payload_copy["exp"] = exp

        payload_b64 = cls._b64_url_encode(json.dumps(payload_copy).encode('utf-8'))

        # Firma HMAC-SHA256
        msg = f"{header_b64}.{payload_b64}".encode('utf-8')
        sig = hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).digest()
        sig_b64 = cls._b64_url_encode(sig)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    @classmethod
    def validar_token_jwt(cls, token: str, secret: str = SECRET_KEY) -> Optional[Dict[str, Any]]:
        """Valida firma y expiración del token JWT. Retorna payload o None si es inválido."""
        if not token or token.count('.') != 2:
            return None
        try:
            h_b64, p_b64, s_b64 = token.split('.')
            msg = f"{h_b64}.{p_b64}".encode('utf-8')
            expected_sig = hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).digest()
            actual_sig = cls._b64_url_decode(s_b64)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return None

            payload = json.loads(cls._b64_url_decode(p_b64).decode('utf-8'))
            exp = payload.get("exp", 0)
            now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
            if now > exp:
                return None  # Expirado

            return payload
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # ALGORITMO TOTP ESTÁNDAR (RFC 6238 / RFC 4226)
    # -------------------------------------------------------------------------
    @classmethod
    def generar_totp(cls, secret_b32: str, intervalo: int = 30, digitos: int = 6, timestamp: Optional[float] = None) -> str:
        """Genera un código TOTP estándar RFC 6238 a partir de un secreto Base32."""
        if timestamp is None:
            timestamp = time.time()
        t = int(timestamp // intervalo)
        key = base64.b32decode(secret_b32.upper())
        counter_bytes = struct.pack(">Q", t)
        mac = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        offset = mac[-1] & 0x0f
        code = (struct.unpack(">I", mac[offset:offset+4])[0] & 0x7fffffff) % (10 ** digitos)
        return str(code).zfill(digitos)

    @classmethod
    def verificar_totp(cls, secret_b32: str, codigo: str, intervalo: int = 30, tolerancia_pasos: int = 1) -> bool:
        """Valida un código TOTP RFC 6238 considerando una ventana de tolerancia frente a desajustes horarios."""
        if not codigo or len(codigo.strip()) != 6:
            return False
        codigo_limpio = codigo.strip()
        now = time.time()
        for paso in range(-tolerancia_pasos, tolerancia_pasos + 1):
            esperado = cls.generar_totp(secret_b32, intervalo=intervalo, timestamp=now + paso * intervalo)
            if hmac.compare_digest(esperado, codigo_limpio):
                return True
        return False

    # -------------------------------------------------------------------------
    # FLUJO DE AUTENTICACIÓN EN DOS PASOS (2FA)
    # -------------------------------------------------------------------------
    @classmethod
    def iniciar_login_2fa(cls, usuario: str, clave_plana: str) -> Optional[Dict[str, Any]]:
        """
        Paso 1: Valida las credenciales de acceso (usuario y clave).
        Si son válidas, genera un desafío 2FA con temp_token firmado y código OTP de 6 dígitos.
        """
        usr = USUARIOS_SISTEMA.get(usuario.strip())
        if not usr:
            return None
        clave_hash = hashlib.sha256(clave_plana.encode()).hexdigest()
        if not hmac.compare_digest(usr["clave_hash"], clave_hash):
            return None

        # Generar código OTP dinámico de 6 dígitos para este desafío
        codigo_otp = f"{secrets.randbelow(900000) + 100000:06d}"
        otp_hash = hashlib.sha256(f"{codigo_otp}:{SECRET_KEY}".encode()).hexdigest()

        # Token temporal de 2FA firmado con expiración corta (5 minutos)
        exp_timestamp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=EXPIRATION_2FA_MINUTES)).timestamp())
        payload_temp = {
            "sub": usr["usuario"],
            "tipo": "2fa_desafio",
            "otp_hash": otp_hash,
            "exp": exp_timestamp
        }
        temp_token = cls.crear_token_jwt(payload_temp)

        tel = usr.get("telefono")
        eml = usr.get("email")
        tel_mascara = f"{tel[:4]} *** ** {tel[-2:]}" if tel and len(tel) > 6 else "+57 *** ***"
        eml_mascara = f"{eml[:3]}***@{eml.split('@')[1]}" if eml and "@" in eml else "***@salud.gov.co"

        return {
            "requiere_2fa": True,
            "temp_token": temp_token,
            "usuario": usr["usuario"],
            "nombre": usr["nombre"],
            "rol": usr["rol"],
            "documento_id": usr.get("documento_id"),
            "profesional_id": usr.get("profesional_id"),
            "telefono_enmascarado": tel_mascara,
            "email_enmascarado": eml_mascara,
            "secret_2fa": usr.get("secret_2fa"),
            "codigo_simulado": codigo_otp,
            "expira_en_segundos": EXPIRATION_2FA_MINUTES * 60,
            "mensaje": "Primer factor (contraseña) verificado con éxito. Ingrese el código de 6 dígitos para completar el acceso."
        }

    @classmethod
    def verificar_segundo_paso_2fa(cls, temp_token: str, codigo_2fa: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Paso 2: Valida el código 2FA suministrado contra el temp_token o contra el TOTP RFC 6238 del usuario.
        Si es correcto, emite el token JWT definitivo con claim 'mfa_verificado: True'.
        """
        payload = cls.validar_token_jwt(temp_token)
        if not payload:
            return False, "Token de verificación 2FA no válido o expirado (401)", None

        if payload.get("tipo") != "2fa_desafio":
            return False, "El token proporcionado no corresponde a un desafío de autenticación en dos pasos", None

        usuario = payload.get("sub", "")
        usr = USUARIOS_SISTEMA.get(usuario)
        if not usr:
            return False, "Usuario no encontrado en el directorio del sistema", None

        codigo_limpio = (codigo_2fa or "").strip()
        if not codigo_limpio or len(codigo_limpio) != 6:
            return False, "El código 2FA debe constar exactamente de 6 dígitos numéricos", None

        # 1. Comprobar contra el OTP generado para esta sesión
        otp_hash_actual = hashlib.sha256(f"{codigo_limpio}:{SECRET_KEY}".encode()).hexdigest()
        codigo_valido = hmac.compare_digest(otp_hash_actual, payload.get("otp_hash", ""))

        # 2. Comprobar alternativamente contra el TOTP estándar RFC 6238 (Google Authenticator)
        if not codigo_valido and usr.get("secret_2fa"):
            if cls.verificar_totp(usr["secret_2fa"], codigo_limpio):
                codigo_valido = True

        if not codigo_valido:
            return False, "Código de verificación en dos pasos (2FA) incorrecto", None

        # Emisión del token JWT definitivo con 2FA acreditado
        final_payload = {
            "sub": usr["usuario"],
            "rol": usr["rol"],
            "nombre": usr["nombre"],
            "documento_id": usr.get("documento_id"),
            "profesional_id": usr.get("profesional_id"),
            "mfa_verificado": True,
            "metodo_2fa": "OTP_TOTP_RFC6238",
            "auth_time": int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        }
        token_definitivo = cls.crear_token_jwt(final_payload)

        return True, "Autenticación en dos pasos exitosa", {
            "token": token_definitivo,
            "usuario": usr["usuario"],
            "nombre": usr["nombre"],
            "rol": usr["rol"],
            "documento_id": usr.get("documento_id"),
            "profesional_id": usr.get("profesional_id"),
            "mfa_verificado": True
        }

    @classmethod
    def regenerar_codigo_desafio(cls, temp_token: str) -> Optional[Dict[str, Any]]:
        """Permite reenviar/generar un nuevo código OTP si el anterior caducó o no llegó."""
        payload = cls.validar_token_jwt(temp_token)
        if not payload or payload.get("tipo") != "2fa_desafio":
            return None

        usuario = payload.get("sub", "")
        usr = USUARIOS_SISTEMA.get(usuario)
        if not usr:
            return None

        nuevo_codigo = f"{secrets.randbelow(900000) + 100000:06d}"
        nuevo_otp_hash = hashlib.sha256(f"{nuevo_codigo}:{SECRET_KEY}".encode()).hexdigest()
        exp_timestamp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=EXPIRATION_2FA_MINUTES)).timestamp())

        payload_temp = {
            "sub": usuario,
            "tipo": "2fa_desafio",
            "otp_hash": nuevo_otp_hash,
            "exp": exp_timestamp
        }
        nuevo_temp_token = cls.crear_token_jwt(payload_temp)

        return {
            "temp_token": nuevo_temp_token,
            "codigo_simulado": nuevo_codigo,
            "expira_en_segundos": EXPIRATION_2FA_MINUTES * 60,
            "mensaje": "Se ha generado y emitido un nuevo código de verificación 2FA."
        }

    @classmethod
    def autenticar_con_ambos_factores(cls, usuario: str, clave_plana: str, codigo_2fa: str) -> Optional[Dict[str, Any]]:
        """Valida credenciales y código 2FA (TOTP RFC 6238) en un solo paso unificado."""
        usr = USUARIOS_SISTEMA.get(usuario.strip())
        if not usr:
            return None
        clave_hash = hashlib.sha256(clave_plana.encode()).hexdigest()
        if not hmac.compare_digest(usr["clave_hash"], clave_hash):
            return None

        codigo_limpio = (codigo_2fa or "").strip()
        if not usr.get("secret_2fa") or not cls.verificar_totp(usr["secret_2fa"], codigo_limpio):
            return None

        final_payload = {
            "sub": usr["usuario"],
            "rol": usr["rol"],
            "nombre": usr["nombre"],
            "documento_id": usr.get("documento_id"),
            "profesional_id": usr.get("profesional_id"),
            "mfa_verificado": True,
            "metodo_2fa": "TOTP_RFC6238_DIRECTO"
        }
        token = cls.crear_token_jwt(final_payload)
        return {
            "token": token,
            "usuario": usr["usuario"],
            "nombre": usr["nombre"],
            "rol": usr["rol"],
            "documento_id": usr.get("documento_id"),
            "profesional_id": usr.get("profesional_id"),
            "mfa_verificado": True
        }

    @classmethod
    def obtener_info_2fa_usuario(cls, usuario: str) -> Optional[Dict[str, Any]]:
        """Retorna detalles de configuración 2FA y URI para aplicaciones autenticadoras."""
        usr = USUARIOS_SISTEMA.get(usuario.strip())
        if not usr:
            return None
        secret = usr.get("secret_2fa", "")
        return {
            "usuario": usr["usuario"],
            "nombre": usr["nombre"],
            "rol": usr["rol"],
            "secret_2fa": secret,
            "totp_uri": f"otpauth://totp/SISDIS:{usr['usuario']}?secret={secret}&issuer=SISDIS_Salud",
            "mfa_habilitado": usr.get("mfa_habilitado", True)
        }

    # -------------------------------------------------------------------------
    # MÉTODO HISTÓRICO / COMPATIBILIDAD CON RBAC EXISTENTE
    # -------------------------------------------------------------------------
    @classmethod
    def autenticar_usuario(cls, usuario: str, clave_plana: str, codigo_2fa: Optional[str] = None, requerir_2fa: bool = False) -> Optional[Dict[str, Any]]:
        """
        Verifica credenciales contra el directorio del sistema.
        - Si requerir_2fa=True y no hay codigo_2fa: devuelve el desafío 2FA (Paso 1).
        - Si codigo_2fa está presente: valida credenciales y código 2FA.
        - Si requerir_2fa=False y no hay codigo_2fa: emite token directo para retrocompatibilidad.
        """
        if requerir_2fa and not codigo_2fa:
            return cls.iniciar_login_2fa(usuario, clave_plana)

        if codigo_2fa:
            return cls.autenticar_con_ambos_factores(usuario, clave_plana, codigo_2fa)

        # Autenticación directa simple (retrocompatibilidad)
        usr = USUARIOS_SISTEMA.get(usuario.strip())
        if not usr:
            return None
        clave_hash = hashlib.sha256(clave_plana.encode()).hexdigest()
        if not hmac.compare_digest(usr["clave_hash"], clave_hash):
            return None

        payload = {
            "sub": usr["usuario"],
            "rol": usr["rol"],
            "nombre": usr["nombre"],
            "documento_id": usr.get("documento_id"),
            "profesional_id": usr.get("profesional_id"),
            "mfa_verificado": False
        }
        token = cls.crear_token_jwt(payload)
        return {
            "token": token,
            "usuario": usr["usuario"],
            "nombre": usr["nombre"],
            "rol": usr["rol"],
            "documento_id": usr.get("documento_id")
        }

    @classmethod
    def verificar_acceso(cls, token: str, roles_permitidos: List[str], documento_solicitado: Optional[int] = None, exigir_2fa: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Valida que el token sea legítimo y tenga permiso para la acción solicitada.
        Opcionalmente verifica que el token haya completado el doble factor (2FA).
        Para rol 'paciente', valida que el documento solicitado coincida exactamente con el suyo.
        """
        payload = cls.validar_token_jwt(token)
        if not payload:
            return False, "Token no proporcionado, inválido o expirado (401)", None

        if exigir_2fa and not payload.get("mfa_verificado", False):
            return False, "Acceso restringido: Se requiere verificación en dos pasos (2FA) completada (403)", payload

        rol_usuario = payload.get("rol", "")
        if rol_usuario not in roles_permitidos:
            return False, f"Acceso denegado: el rol '{rol_usuario}' no tiene privilegios para esta operación (403)", payload

        # Regla especial de confidencialidad para paciente: solo ve su historia
        if rol_usuario == "paciente":
            doc_paciente = payload.get("documento_id")
            if documento_solicitado is not None and int(documento_solicitado) != int(doc_paciente):
                return False, f"Acceso denegado: el paciente no puede acceder a historias de otros pacientes (403)", payload

        return True, "Acceso concedido", payload
