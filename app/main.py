#!/usr/bin/env python3
"""
main.py — Aplicación Web y API Gateway de la Plataforma
Sirve vistas separadas e independientes por rol con control RBAC estricto:
- /login: Portal de autenticación con verificación en dos pasos (2FA).
- /paciente: Portal exclusivo del paciente (historia propia y descarga FHIR).
- /admision: Portal exclusivo de admisión (triage y búsqueda en sedes).
- /medico: Estación médica asistencial (diagnósticos CIE-10 y sellos clínicos).
- /auditor: Tablero de auditoría criptográfica SHA-256, monitoreo y reporte normativo (Res. 866).
- /demo: Vista unificada para demostración académica.
"""

from fastapi import FastAPI, Request, Response, HTTPException, Depends, status, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import sys
import datetime
import time

# Asegurar módulos locales
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.seguridad import GestorSeguridad
from app.consulta_unificada import MotorConsultaUnificada
from fhir.normalizador import NormalizadorFHIR
from hsb.service import HSBService

app = FastAPI(
    title="Plataforma de Interoperabilidad Clínica — Vistas Aisladas por Rol con 2FA",
    description="Aplicación web multi-rol para Paciente, Admisionista, Médico y Auditoría",
    version="1.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Plantillas HTML
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Instancias compartidas del motor de consulta y HSB
motor_consulta = MotorConsultaUnificada()
ref_csv_path = os.path.join(os.path.dirname(__file__), '..', 'ejemplos', '05_ref_terminologia.csv')
hsb_service = HSBService(ref_csv_path=ref_csv_path)

# Modelos Pydantic de entrada
class LoginRequest(BaseModel):
    usuario: str
    clave: str
    codigo_2fa: Optional[str] = None

class Verificar2FARequest(BaseModel):
    temp_token: str
    codigo_2fa: str

class Reenviar2FARequest(BaseModel):
    temp_token: str

class AdmisionRequest(BaseModel):
    documento_id: int
    sede_id: int
    triage: str
    motivo: str

class AtencionMedicoRequest(BaseModel):
    documento_id: int
    sede_id: int
    cie10: str
    dx_desc: str
    tecnologia: str
    egreso: str

def obtener_payload_autenticado(request: Request) -> Optional[Dict[str, Any]]:
    """Extrae y valida el token JWT desde cookies, header Authorization o query params."""
    # 1. Comprobar en Cookie de sesión
    token = request.cookies.get("sisdis_token")

    # 2. Comprobar en Header Authorization: Bearer <token>
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    # 3. Comprobar en Query param ?token=
    if not token:
        token = request.query_params.get("token")

    if not token:
        return None

    return GestorSeguridad.validar_token_jwt(token)

# -----------------------------------------------------------------------------
# RUTAS DE INTERFAZ WEB POR ROL (RBAC ESTRICTO)
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Enrutador raíz: redirige a la vista correspondiente al rol o al login si no hay sesión."""
    payload = obtener_payload_autenticado(request)
    if not payload:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    rol = payload.get("rol")
    if rol == "paciente":
        return RedirectResponse(url="/paciente", status_code=status.HTTP_302_FOUND)
    elif rol == "admisionista":
        return RedirectResponse(url="/admision", status_code=status.HTTP_302_FOUND)
    elif rol == "medico":
        return RedirectResponse(url="/medico", status_code=status.HTTP_302_FOUND)
    elif rol == "auditor":
        return RedirectResponse(url="/auditor", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Portal de autenticación y verificación en dos pasos (2FA)."""
    payload = obtener_payload_autenticado(request)
    if payload:
        rol = payload.get("rol")
        dest = "/paciente" if rol == "paciente" else ("/admision" if rol == "admisionista" else ("/medico" if rol == "medico" else "/auditor"))
        return RedirectResponse(url=dest, status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/logout")
def logout(response: Response):
    """Cierra la sesión limpiando la cookie y redirige al login."""
    res = RedirectResponse(url="/login?msg=sesion_cerrada", status_code=status.HTTP_302_FOUND)
    res.delete_cookie("sisdis_token")
    return res

@app.get("/paciente", response_class=HTMLResponse)
async def vista_paciente(request: Request):
    """Vista exclusiva para pacientes: Historia Clínica Unificada y descarga FHIR R4."""
    payload = obtener_payload_autenticado(request)
    if not payload:
        return RedirectResponse(url="/login?error=no_auth&next=/paciente", status_code=status.HTTP_302_FOUND)

    rol = payload.get("rol", "")
    if rol not in ["paciente", "medico", "auditor"]:
        return templates.TemplateResponse(request=request, name="error_403.html", context={
            "rol_usuario": rol,
            "recurso": "Portal del Paciente (/paciente)",
            "mensaje": f"El rol '{rol}' no cuenta con permisos para acceder al portal del paciente."
        }, status_code=403)

    return templates.TemplateResponse(request=request, name="paciente.html", context={
        "usuario": payload.get("sub"),
        "nombre": payload.get("nombre"),
        "rol": rol,
        "documento_id": payload.get("documento_id") or 1001
    })

@app.get("/admision", response_class=HTMLResponse)
async def vista_admision(request: Request):
    """Vista exclusiva para admisionistas: Triage y búsqueda administrativa en sedes."""
    payload = obtener_payload_autenticado(request)
    if not payload:
        return RedirectResponse(url="/login?error=no_auth&next=/admision", status_code=status.HTTP_302_FOUND)

    rol = payload.get("rol", "")
    if rol not in ["admisionista", "auditor"]:
        return templates.TemplateResponse(request=request, name="error_403.html", context={
            "rol_usuario": rol,
            "recurso": "Módulo de Admisión y Triage (/admision)",
            "mensaje": f"Acceso denegado: El rol '{rol}' no tiene privilegios de personal de admisión."
        }, status_code=403)

    return templates.TemplateResponse(request=request, name="admision.html", context={
        "usuario": payload.get("sub"),
        "nombre": payload.get("nombre"),
        "rol": rol
    })

@app.get("/medico", response_class=HTMLResponse)
async def vista_medico(request: Request):
    """Vista exclusiva para médicos: Consulta integral, diagnósticos CIE-10 y sellos."""
    payload = obtener_payload_autenticado(request)
    if not payload:
        return RedirectResponse(url="/login?error=no_auth&next=/medico", status_code=status.HTTP_302_FOUND)

    rol = payload.get("rol", "")
    if rol not in ["medico", "auditor"]:
        return templates.TemplateResponse(request=request, name="error_403.html", context={
            "rol_usuario": rol,
            "recurso": "Estación Médica Asistencial (/medico)",
            "mensaje": f"Acceso denegado: El rol '{rol}' no tiene privilegios clínicos para acceder a la estación médica."
        }, status_code=403)

    return templates.TemplateResponse(request=request, name="medico.html", context={
        "usuario": payload.get("sub"),
        "nombre": payload.get("nombre"),
        "rol": rol,
        "profesional_id": payload.get("profesional_id", "MED-01")
    })

@app.get("/auditor", response_class=HTMLResponse)
@app.get("/reporte", response_class=HTMLResponse)
@app.get("/monitoreo", response_class=HTMLResponse)
async def vista_auditor(request: Request):
    """Vista exclusiva para auditores: Integridad criptográfica, métricas y 57 campos normativos."""
    payload = obtener_payload_autenticado(request)
    if not payload:
        return RedirectResponse(url="/login?error=no_auth&next=/auditor", status_code=status.HTTP_302_FOUND)

    rol = payload.get("rol", "")
    if rol not in ["auditor"]:
        return templates.TemplateResponse(request=request, name="error_403.html", context={
            "rol_usuario": rol,
            "recurso": "Tablero de Auditoría Institucional (/auditor)",
            "mensaje": f"Acceso denegado: El rol '{rol}' no tiene privilegios de auditoría institucional."
        }, status_code=403)

    return templates.TemplateResponse(request=request, name="auditor.html", context={
        "usuario": payload.get("sub"),
        "nombre": payload.get("nombre"),
        "rol": rol
    })

@app.get("/demo", response_class=HTMLResponse)
async def vista_demo(request: Request):
    """Vista unificada de demostración académica con pestañas."""
    index_file = os.path.join(templates_dir, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
def health():
    """Endpoint de salud del servicio web."""
    return {
        "status": "UP",
        "service": "web-app-gateway",
        "dependencias": {
            "hsb_service": "conectado",
            "motor_consulta": "activo"
        }
    }

@app.get("/metrics")
def metrics():
    """Métricas operativas del servicio web."""
    metricas_hsb = hsb_service.obtener_metricas()
    cobertura = motor_consulta.obtener_cobertura_fhir_red()
    estado_sedes = motor_consulta.obtener_estado_sedes()
    nodos_activos = sum(1 for s in estado_sedes.values() if s["disponible"])
    return {
        "hsb_metricas": metricas_hsb,
        "cobertura_red": cobertura,
        "nodos_activos": nodos_activos,
        "sedes": estado_sedes
    }

@app.get("/api/sedes/estado")
def api_estado_sedes():
    """Retorna la disponibilidad en tiempo real de cada contenedor de sede."""
    return motor_consulta.obtener_estado_sedes()

# -----------------------------------------------------------------------------
# AUTENTICACIÓN Y SEGURIDAD RBAC / 2FA
# -----------------------------------------------------------------------------
@app.post("/api/auth/login")
def login(req: LoginRequest, response: Response):
    """
    Autenticación en dos pasos (2FA):
    - Si se envía codigo_2fa: valida ambos factores directamente y establece cookie de sesión.
    - Si NO se envía codigo_2fa: valida contraseña (Paso 1) y genera desafío con temp_token (Paso 2).
    """
    if req.codigo_2fa:
        auth = GestorSeguridad.autenticar_con_ambos_factores(req.usuario, req.clave, req.codigo_2fa)
        if not auth:
            hsb_service.registrar_evento_auditoria(
                actor=req.usuario,
                rol="desconocido",
                accion="LOGIN_2FA_DIRECTO_FALLIDO",
                sede_id=0,
                recurso="SISTEMA",
                detalle=f"Fallo en autenticación directa 2FA para usuario {req.usuario}",
                resultado="DENEGADO"
            )
            raise HTTPException(status_code=401, detail="Credenciales o código 2FA incorrectos")

        response.set_cookie(key="sisdis_token", value=auth["token"], httponly=False, samesite="lax", max_age=28800)
        hsb_service.registrar_evento_auditoria(
            actor=req.usuario,
            rol=auth["rol"],
            accion="LOGIN_2FA_EXITOSO",
            sede_id=0,
            recurso="SISTEMA",
            detalle=f"Inicio de sesión exitoso con 2FA completado como {auth['rol']}",
            resultado="EXITOSO"
        )
        return auth

    desafio = GestorSeguridad.iniciar_login_2fa(req.usuario, req.clave)
    if not desafio:
        hsb_service.registrar_evento_auditoria(
            actor=req.usuario,
            rol="desconocido",
            accion="LOGIN_FALLIDO_PASO1",
            sede_id=0,
            recurso="SISTEMA",
            detalle=f"Intento de autenticación fallido para {req.usuario}: contraseña incorrecta",
            resultado="DENEGADO"
        )
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    hsb_service.registrar_evento_auditoria(
        actor=req.usuario,
        rol=desafio["rol"],
        accion="LOGIN_PASO1_OK",
        sede_id=0,
        recurso="SISTEMA",
        detalle=f"Paso 1 completado para {req.usuario} ({desafio['rol']}). Desafío 2FA emitido.",
        resultado="EXITOSO"
    )
    return desafio

@app.post("/api/auth/verificar-2fa")
def api_verificar_2fa(req: Verificar2FARequest, response: Response):
    """
    Paso 2 de autenticación:
    Valida el código de 6 dígitos (OTP o TOTP RFC 6238), emite el JWT definitivo y fija la cookie de sesión.
    """
    exito, mensaje, auth = GestorSeguridad.verificar_segundo_paso_2fa(req.temp_token, req.codigo_2fa)
    if not exito or not auth:
        hsb_service.registrar_evento_auditoria(
            actor="2FA_DESAFIO",
            rol="desconocido",
            accion="LOGIN_2FA_FALLIDO",
            sede_id=0,
            recurso="SISTEMA",
            detalle=f"Fallo en verificación 2FA: {mensaje}",
            resultado="DENEGADO"
        )
        raise HTTPException(status_code=401, detail=mensaje)

    # Establecer cookie de sesión para navegación directa por pestañas/URLs protegidas
    response.set_cookie(key="sisdis_token", value=auth["token"], httponly=False, samesite="lax", max_age=28800)

    hsb_service.registrar_evento_auditoria(
        actor=auth["usuario"],
        rol=auth["rol"],
        accion="LOGIN_2FA_EXITOSO",
        sede_id=0,
        recurso="SISTEMA",
        detalle=f"Segundo factor (2FA) superado con éxito por {auth['usuario']} ({auth['rol']}). Acceso otorgado.",
        resultado="EXITOSO"
    )
    return auth

@app.post("/api/auth/reenviar-2fa")
def api_reenviar_2fa(req: Reenviar2FARequest):
    """Regenera y emite un nuevo código OTP para el desafío temporal."""
    resultado = GestorSeguridad.regenerar_codigo_desafio(req.temp_token)
    if not resultado:
        raise HTTPException(status_code=400, detail="Token temporal de 2FA inválido o expirado")
    return resultado

@app.get("/api/auth/2fa/info/{usuario}")
def api_info_2fa(usuario: str):
    """Retorna la configuración 2FA y URI TOTP para vincular con Google Authenticator."""
    info = GestorSeguridad.obtener_info_2fa_usuario(usuario)
    if not info:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return info

# -----------------------------------------------------------------------------
# VISTA 1: PACIENTE
# -----------------------------------------------------------------------------
@app.get("/api/paciente/{documento_id}/historia")
def obtener_historia_paciente(documento_id: int, request: Request):
    """Consulta la historia unificada en las 3 sedes con validación de confidencialidad y Habeas Data."""
    payload = obtener_payload_autenticado(request)
    if payload:
        rol = payload.get("rol", "")
        if rol == "paciente":
            doc_pac = payload.get("documento_id")
            if doc_pac and int(doc_pac) != int(documento_id):
                hsb_service.registrar_evento_auditoria(
                    actor=str(payload.get("sub")),
                    rol="paciente",
                    accion="ACCESO_DENEGADO_HABEAS_DATA",
                    sede_id=0,
                    recurso=f"Patient/pac-{documento_id}",
                    detalle=f"Intento ilegítimo de consultar historia ajena del documento {documento_id}",
                    resultado="DENEGADO"
                )
                raise HTTPException(status_code=403, detail="Acceso denegado: el paciente no puede acceder a historias de otros pacientes (403)")
        elif rol not in ["paciente", "medico", "auditor"]:
            raise HTTPException(status_code=403, detail=f"Acceso denegado: el rol '{rol}' no tiene permisos para consultar historias clínicas (403)")

    hsb_service.registrar_evento_auditoria(
        actor=str(payload.get("sub") if payload else documento_id),
        rol=str(payload.get("rol") if payload else "paciente"),
        accion="CONSULTA_HC",
        sede_id=0,
        recurso=f"Patient/pac-{documento_id}",
        detalle=f"Consulta de historia unificada multi-sede para documento {documento_id}",
        resultado="EXITOSO"
    )
    resultado = motor_consulta.consultar_historia_unificada(documento_id)
    return resultado

@app.get("/api/paciente/{documento_id}/bundle-fhir")
def descargar_bundle_fhir(documento_id: int, request: Request):
    """Genera y descarga el Bundle FHIR R4 con validación de rol."""
    payload = obtener_payload_autenticado(request)
    if payload and payload.get("rol") == "paciente":
        doc_pac = payload.get("documento_id")
        if doc_pac and int(doc_pac) != int(documento_id):
            raise HTTPException(status_code=403, detail="Acceso denegado: no puede descargar el Bundle de otro paciente")

    historia = motor_consulta.consultar_historia_unificada(documento_id)
    paciente = historia.get("paciente", {})
    recursos = []

    pac_res = NormalizadorFHIR.crear_recurso_patient(
        documento=str(documento_id),
        nombre_completo=paciente.get("nombre", f"Paciente {documento_id}"),
        sexo=paciente.get("sexo", "M"),
        fecha_nacimiento=paciente.get("nacimiento")
    )
    recursos.append(pac_res)

    for at in historia.get("atenciones", []):
        enc_id = f"enc-{at.get('atencion_id', 1)}"
        enc_res = NormalizadorFHIR.crear_recurso_encounter(
            encounter_id=enc_id,
            patient_id=pac_res["id"],
            clase="O",
            fecha_ingreso=at.get("fecha"),
            sede_nombre=at.get("sede_nombre", "Sede Hospitalaria"),
            profesional=at.get("profesional"),
            triage=at.get("triage")
        )
        recursos.append(enc_res)

        for dx in at.get("diagnosticos", []):
            cond_res = NormalizadorFHIR.crear_recurso_condition(
                condition_id=f"{documento_id}-{dx.get('cie10')}",
                patient_id=pac_res["id"],
                encounter_id=enc_res["id"],
                cie10=dx.get("cie10"),
                descripcion=dx.get("descripcion", ""),
                fecha=at.get("fecha")
            )
            recursos.append(cond_res)

        for lab in at.get("laboratorios", []):
            obs_res = NormalizadorFHIR.crear_recurso_observation(
                obs_id=f"{documento_id}-{lab.get('codigo')}",
                patient_id=pac_res["id"],
                encounter_id=enc_res["id"],
                loinc_code=lab.get("codigo"),
                descripcion=lab.get("nombre", ""),
                valor=lab.get("valor", ""),
                unidad=lab.get("unidad", "")
            )
            recursos.append(obs_res)

    bundle = NormalizadorFHIR.empaquetar_en_bundle(recursos)
    return bundle

# -----------------------------------------------------------------------------
# VISTA 2: ADMISIONISTA
# -----------------------------------------------------------------------------
@app.get("/api/admision/buscar/{documento_id}")
def admision_buscar(documento_id: int):
    """Indica en qué sedes existe el paciente sin revelar contenido clínico confidencial."""
    doc = int(documento_id)
    sedes_info = []
    for s_id in (1, 2, 3):
        existe = doc in motor_consulta.datos_simulados_locales.get(s_id, {})
        sedes_info.append({
            "sede_id": s_id,
            "nombre": motor_consulta.config_sedes[s_id]["nombre"],
            "ciudad": motor_consulta.config_sedes[s_id]["ciudad"],
            "existe": existe
        })
    return {"documento_id": doc, "sedes": sedes_info}

@app.post("/api/admision/admitir")
def admision_admitir(req: AdmisionRequest, request: Request):
    """Registra admisión con triage y envía el mensaje al HSB."""
    payload = obtener_payload_autenticado(request)
    if payload and payload.get("rol") not in ["admisionista", "auditor"]:
        raise HTTPException(status_code=403, detail="Acceso denegado: solo personal de admisión puede registrar triages (403)")

    id_control = f"MSG-ADM-{req.documento_id}-{int(req.sede_id)}-{int(time.time())}"
    actor = payload.get("sub") if payload else "admision1"
    t_now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # --- Persistir paciente en datos simulados si no existe ---
    doc = int(req.documento_id)
    sid = int(req.sede_id)
    if sid not in motor_consulta.datos_simulados_locales:
        motor_consulta.datos_simulados_locales[sid] = {}
    if doc not in motor_consulta.datos_simulados_locales[sid]:
        motor_consulta.datos_simulados_locales[sid][doc] = {
            "paciente": {
                "documento_id": doc,
                "nombre": f"Paciente {doc}",
                "sexo": "M",
                "nacimiento": None,
                "fhir_patient_id": f"pac-{doc}"
            },
            "atenciones": [{
                "atencion_id": int(time.time()),
                "sede_id": sid,
                "sede_nombre": motor_consulta.config_sedes.get(sid, {}).get("nombre", f"Sede {sid}"),
                "fecha": t_now,
                "triage": req.triage,
                "profesional": actor,
                "diagnosticos": [],
                "laboratorios": []
            }]
        }
    else:
        # Paciente ya existe: agregar la atención de admisión
        motor_consulta.datos_simulados_locales[sid][doc]["atenciones"].append({
            "atencion_id": int(time.time()),
            "sede_id": sid,
            "sede_nombre": motor_consulta.config_sedes.get(sid, {}).get("nombre", f"Sede {sid}"),
            "fecha": t_now,
            "triage": req.triage,
            "profesional": actor,
            "diagnosticos": [],
            "laboratorios": []
        })

    # --- Registrar mensaje en HSB para la tabla de mensajería ---
    hsb_service.mensajes_db[id_control] = {
        "id": id_control,
        "id_control": id_control,
        "formato": "ADM",
        "sede_id": sid,
        "sede": sid,
        "documento": str(doc),
        "paciente": str(doc),
        "estado": "admitido",
        "status": "admitido",
        "triage": req.triage,
        "motivo": req.motivo,
        "timestamp": t_now
    }

    hsb_service.registrar_evento_auditoria(
        actor=actor,
        rol="admisionista",
        accion="REGISTRO_TRIAGE",
        sede_id=req.sede_id,
        recurso=f"Encounter/enc-{id_control}",
        detalle=f"Admisión en Sede {req.sede_id} con Triage {req.triage}. Motivo: {req.motivo}",
        resultado="EXITOSO"
    )
    return {
        "status": "admitido",
        "id_control": id_control,
        "mensaje": f"Paciente {req.documento_id} admitido en sede {req.sede_id} con triage {req.triage}"
    }

# -----------------------------------------------------------------------------
# VISTA 3: MÉDICO
# -----------------------------------------------------------------------------
@app.post("/api/medico/atencion")
def medico_registrar_atencion(req: AtencionMedicoRequest, request: Request):
    """Registra atención médica con emisión de sello de integridad."""
    payload = obtener_payload_autenticado(request)
    if payload and payload.get("rol") not in ["medico", "auditor"]:
        raise HTTPException(status_code=403, detail="Acceso denegado: solo el personal médico puede registrar diagnósticos clínicos (403)")

    prof_id = (payload.get("profesional_id") if payload else None) or "MED-01"
    resultado = motor_consulta.registrar_atencion_medico(
        documento_id=req.documento_id,
        sede_id=req.sede_id,
        profesional_id=prof_id,
        cie10=req.cie10,
        dx_desc=req.dx_desc,
        tecnologia=req.tecnologia,
        egreso_destino=req.egreso
    )

    # --- Registrar mensaje en HSB para la tabla de mensajería ---
    t_now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    id_control_med = f"MSG-MED-{req.documento_id}-{int(req.sede_id)}-{int(time.time())}"
    hsb_service.mensajes_db[id_control_med] = {
        "id": id_control_med,
        "id_control": id_control_med,
        "formato": "MED",
        "sede_id": int(req.sede_id),
        "sede": int(req.sede_id),
        "documento": str(req.documento_id),
        "paciente": str(req.documento_id),
        "estado": "registrado",
        "status": "registrado",
        "cie10": req.cie10,
        "dx_desc": req.dx_desc,
        "timestamp": t_now
    }

    hsb_service.registrar_evento_auditoria(
        actor=prof_id,
        rol="medico",
        accion="REGISTRO_ATENCION_CLINICA",
        sede_id=req.sede_id,
        recurso=f"Condition/cond-{req.documento_id}-{req.cie10}",
        detalle=f"Diagnóstico {req.cie10} ({req.dx_desc}) y egreso a {req.egreso}. Sello: {resultado['sello_integridad'][:12]}...",
        resultado="EXITOSO"
    )
    return resultado

# -----------------------------------------------------------------------------
# VISTA 5: TABLERO DE ESTADO & MONITOREO
# -----------------------------------------------------------------------------
@app.get("/hsb/mensajes")
def hsb_mensajes():
    todos = list(hsb_service.mensajes_db.values())
    return {"total": len(todos), "mensajes": todos}

@app.post("/hsb/auditoria/verificar")
def verificar_auditoria_endpoint():
    return hsb_service.verificar_integridad_auditoria()

@app.post("/hsb/auditoria/alterar")
def simular_alteracion_endpoint(evento_id: int = Query(1)):
    for ev in hsb_service.auditoria_cadena:
        if ev["evento_id"] == evento_id:
            ev["detalle"] = ev["detalle"] + " [DATO_ALTERADO_ILEGITIMAMENTE]"
            return {"status": "alterado", "evento_id": evento_id}
    return {"status": "no_encontrado"}

if __name__ == '__main__':
    import uvicorn
    puerto = int(os.environ.get("APP_PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=puerto)
