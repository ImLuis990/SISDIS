#!/usr/bin/env python3
"""
seguridad.py — Autenticación JWT y Control de Acceso Basado en Roles (RBAC)
Maneja emisión y validación de tokens JWT firmados, control de permisos para los 4 roles:
- paciente: solo accede a su propia historia clínica y auditoría de accesos.
- admisionista: busca pacientes, admite con triage, ve estado del bus (sin datos clínicos).
- medico: consulta HC completa, registra diagnósticos CIE-10, órdenes y egreso clínico.
- auditor: consulta reportes, métricas globales y verifica integridad de la auditoría.
"""

from typing import Optional, Dict, Any, List
import datetime
import hashlib
import hmac
import base64
import json
import os

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "sisdis_super_secret_jwt_key_2026_salud_interoperable")
ALGORITHM = "HS256"
EXPIRATION_HOURS = 8

# Base de usuarios y credenciales de prueba preconfiguradas
USUARIOS_SISTEMA: Dict[str, Dict[str, Any]] = {
    "1001": {
        "usuario": "1001",
        "clave_hash": hashlib.sha256("paciente123".encode()).hexdigest(),
        "nombre": "Carlos Pérez",
        "rol": "paciente",
        "documento_id": 1001
    },
    "1007": {
        "usuario": "1007",
        "clave_hash": hashlib.sha256("paciente123".encode()).hexdigest(),
        "nombre": "Andrea Rojas",
        "rol": "paciente",
        "documento_id": 1007
    },
    "admision1": {
        "usuario": "admision1",
        "clave_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "nombre": "Marta Gómez (Admisión)",
        "rol": "admisionista",
        "documento_id": None
    },
    "medico1": {
        "usuario": "medico1",
        "clave_hash": hashlib.sha256("medico123".encode()).hexdigest(),
        "nombre": "Dra. Laura Vega",
        "rol": "medico",
        "profesional_id": "MED-01",
        "documento_id": None
    },
    "auditor1": {
        "usuario": "auditor1",
        "clave_hash": hashlib.sha256("auditor123".encode()).hexdigest(),
        "nombre": "Lic. Roberto Blanco (Auditor)",
        "rol": "auditor",
        "documento_id": None
    }
}

class GestorSeguridad:
    """Manejo de tokens JWT y validaciones criptográficas sin dependencias externas pesadas."""

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
    def crear_token_jwt(cls, payload: Dict[str, Any], secret: str = SECRET_KEY) -> str:
        """Emite un token JWT firmado con HMAC-SHA256."""
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = cls._b64_url_encode(json.dumps(header).encode('utf-8'))

        # Agregar expiración
        exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=EXPIRATION_HOURS)).timestamp())
        payload_copy = dict(payload)
        payload_copy["exp"] = exp
        payload_b64 = cls._b64_url_encode(json.dumps(payload_copy).encode('utf-8'))

        # Firma
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
                return None # Expirado

            return payload
        except Exception:
            return None

    @classmethod
    def autenticar_usuario(cls, usuario: str, clave_plana: str) -> Optional[Dict[str, Any]]:
        """Verifica credenciales contra el directorio del sistema y emite token."""
        usr = USUARIOS_SISTEMA.get(usuario.strip())
        if not usr:
            return None
        clave_hash = hashlib.sha256(clave_plana.encode()).hexdigest()
        if not hmac.compare_digest(usr["clave_hash"], clave_hash):
            return None

        # Generar token
        payload = {
            "sub": usr["usuario"],
            "rol": usr["rol"],
            "nombre": usr["nombre"],
            "documento_id": usr.get("documento_id"),
            "profesional_id": usr.get("profesional_id")
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
    def verificar_acceso(cls, token: str, roles_permitidos: List[str], documento_solicitado: Optional[int] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Valida que el token sea legítimo y tenga permiso para la acción solicitada.
        Para rol 'paciente', valida que el documento solicitado coincida exactamente con el suyo.
        """
        payload = cls.validar_token_jwt(token)
        if not payload:
            return False, "Token no proporcionado, inválido o expirado (401)", None

        rol_usuario = payload.get("rol", "")
        if rol_usuario not in roles_permitidos:
            return False, f"Acceso denegado: el rol '{rol_usuario}' no tiene privilegios para esta operación (403)", payload

        # Regla especial de confidencialidad para paciente: solo ve su historia
        if rol_usuario == "paciente":
            doc_paciente = payload.get("documento_id")
            if documento_solicitado is not None and int(documento_solicitado) != int(doc_paciente):
                return False, f"Acceso denegado: el paciente no puede acceder a historias de otros pacientes (403)", payload

        return True, "Acceso concedido", payload
