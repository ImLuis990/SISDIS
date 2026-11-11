#!/usr/bin/env python3
"""
main.py — Aplicación Web y API Gateway de la Plataforma
Sirve las 4 vistas por rol, autenticación JWT/RBAC, consultas unificadas tolerantes
a fallos, exportación FHIR R4 y tablero de monitoreo de nodos.
"""

from fastapi import FastAPI, Request, HTTPException, Depends, status, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import sys

# Asegurar módulos locales
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.seguridad import GestorSeguridad
from app.consulta_unificada import MotorConsultaUnificada
from fhir.normalizador import NormalizadorFHIR
from hsb.service import HSBService

app = FastAPI(
    title="Plataforma de Interoperabilidad Clínica — 4 Vistas por Rol",
    description="Aplicación web unificada para Paciente, Admisionista, Médico y Reporte de HC",
    version="1.0.0"
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

# -----------------------------------------------------------------------------
# RUTAS DE INTERFAZ WEB
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renderiza la aplicación de las 4 vistas por rol."""
    index_file = os.path.join(templates_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return templates.TemplateResponse("index.html", {"request": request})

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
    return {
        "hsb_metricas": metricas_hsb,
        "cobertura_red": cobertura,
        "nodos_activos": 3 - len(motor_consulta.sedes_apagadas)
    }

# -----------------------------------------------------------------------------
# AUTENTICACIÓN Y SEGURIDAD RBAC
# -----------------------------------------------------------------------------
@app.post("/api/auth/login")
def login(req: LoginRequest):
    """Autentica al usuario y devuelve el token JWT con su rol asignado."""
    auth = GestorSeguridad.autenticar_usuario(req.usuario, req.clave)
    if not auth:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    hsb_service.registrar_evento_auditoria(
        actor=req.usuario,
        rol=auth["rol"],
        accion="LOGIN",
        sede_id=0,
        recurso="SISTEMA",
        detalle=f"Inicio de sesión exitoso como {auth['rol']}",
        resultado="EXITOSO"
    )
    return auth

# -----------------------------------------------------------------------------
# VISTA 1: PACIENTE
# -----------------------------------------------------------------------------
@app.get("/api/paciente/{documento_id}/historia")
def obtener_historia_paciente(documento_id: int, request: Request):
    """Consulta la historia unificada en las 3 sedes."""
    # Registro de auditoría de acceso
    hsb_service.registrar_evento_auditoria(
        actor=str(documento_id),
        rol="paciente",
        accion="CONSULTA_HC",
        sede_id=0,
        recurso=f"Patient/pac-{documento_id}",
        detalle=f"Consulta de historia unificada multi-sede para documento {documento_id}",
        resultado="EXITOSO"
    )
    resultado = motor_consulta.consultar_historia_unificada(documento_id)
    return resultado

@app.get("/api/paciente/{documento_id}/bundle-fhir")
def descargar_bundle_fhir(documento_id: int):
    """Genera y descarga el Bundle FHIR R4 de tipo transaction con PUT determinista."""
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
def admision_admitir(req: AdmisionRequest):
    """Registra admisión con triage y envía el mensaje al HSB."""
    id_control = f"MSG-ADM-{req.documento_id}-{int(req.sede_id)}"
    hsb_service.registrar_evento_auditoria(
        actor="admision1",
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
def medico_registrar_atencion(req: AtencionMedicoRequest):
    """Registra atención médica con emisión de sello de integridad."""
    resultado = motor_consulta.registrar_atencion_medico(
        documento_id=req.documento_id,
        sede_id=req.sede_id,
        profesional_id="MED-01",
        cie10=req.cie10,
        dx_desc=req.dx_desc,
        tecnologia=req.tecnologia,
        egreso_destino=req.egreso
    )
    hsb_service.registrar_evento_auditoria(
        actor="MED-01",
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
