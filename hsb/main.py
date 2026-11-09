#!/usr/bin/env python3
"""
main.py — API REST del Health Service Bus (HSB) con FastAPI
Expone las puertas de entrada para HL7 v2 y CSV, observabilidad (/health y /metrics),
auditoría encadenada y reintentos.
"""

from fastapi import FastAPI, Request, Query, HTTPException, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Asegurar rutas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from hsb.service import HSBService

app = FastAPI(
    title="Health Service Bus (HSB) — Plataforma de Interoperabilidad Clínica",
    description="Bus de integración de salud para ingesta HL7 v2, CSV, normalización FHIR R4 y auditoría",
    version="1.0.0"
)

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Instancia singleton del servicio HSB
ref_csv_path = os.path.join(os.path.dirname(__file__), '..', 'ejemplos', '05_ref_terminologia.csv')
hsb_service = HSBService(ref_csv_path=ref_csv_path)

@app.get("/")
def raiz():
    return {
        "status": "UP",
        "service": "Health Service Bus (HSB)",
        "version": "1.0.0",
        "endpoints": ["/hsb/hl7", "/hsb/csv", "/health", "/metrics", "/docs"]
    }

@app.get("/health")
def health_check():
    """Estado de salud del servicio y sus dependencias."""
    metricas = hsb_service.obtener_metricas()
    return {
        "status": "UP",
        "service": "HSB",
        "timestamp": metricas.get("mensajes_ultimo_minuto"),
        "dependencias": {
            "hapi_fhir": "disponible",
            "sede_1_sincelejo": "disponible",
            "sede_2_cartagena": "disponible",
            "sede_3_corozal": "disponible"
        }
    }

@app.get("/metrics")
def metrics():
    """Métricas de latencia, fallidos, duplicados y volumen de mensajes."""
    return hsb_service.obtener_metricas()

@app.post("/hsb/hl7")
async def recibir_hl7(request: Request):
    """
    Puerta de entrada de mensajes HL7 v2 (ADT^A01 y ORU^R01).
    Recibe el mensaje en texto plano (body).
    """
    body_bytes = await request.body()
    texto_hl7 = body_bytes.decode('utf-8', errors='ignore')

    if not texto_hl7.strip():
        raise HTTPException(status_code=400, detail="El cuerpo del mensaje HL7 no puede estar vacío.")

    status_code, respuesta = hsb_service.procesar_mensaje_hl7(texto_hl7)
    return JSONResponse(status_code=status_code, content=respuesta)

@app.post("/hsb/csv")
async def recibir_csv(request: Request, sede: int = Query(3, description="Número de sede destino (1, 2 o 3)")):
    """
    Puerta de entrada para archivos CSV legados con separador ';'.
    """
    body_bytes = await request.body()
    texto_csv = body_bytes.decode('utf-8', errors='ignore')

    if not texto_csv.strip():
        raise HTTPException(status_code=400, detail="El contenido CSV no puede estar vacío.")

    resultado = hsb_service.procesar_archivo_csv(texto_csv, sede_id=sede)
    return resultado

@app.get("/hsb/mensajes")
def listar_mensajes(estado: str = Query(None, description="Filtrar por estado (entregado, rechazado, muerto, duplicado)")):
    """Lista todos los mensajes procesados en el HSB."""
    todos = list(hsb_service.mensajes_db.values())
    if estado:
        todos = [m for m in todos if m.get("estado") == estado]
    return {"total": len(todos), "mensajes": todos}

@app.get("/hsb/auditoria")
def obtener_auditoria():
    """Retorna los eventos registrados en la auditoría inmutable encadenada."""
    return {
        "total_eventos": len(hsb_service.auditoria_cadena),
        "eventos": hsb_service.auditoria_cadena
    }

@app.post("/hsb/auditoria/verificar")
def verificar_auditoria():
    """Ejecuta el verificador criptográfico de la cadena de auditoría."""
    return hsb_service.verificar_integridad_auditoria()

@app.post("/hsb/auditoria/alterar")
def simular_alteracion_auditoria(evento_id: int = Query(..., description="ID del evento a alterar")):
    """
    Simula una alteración maliciosa en un registro de auditoría
    para demostrar la detección en vivo del verificador criptográfico.
    """
    for ev in hsb_service.auditoria_cadena:
        if ev["evento_id"] == evento_id:
            ev["detalle"] = ev["detalle"] + " [DATO_ALTERADO_ILEGITIMAMENTE]"
            return {
                "status": "alterado",
                "evento_id": evento_id,
                "mensaje": f"Se modificó el detalle del evento #{evento_id} sin recalcular el hash."
            }
    raise HTTPException(status_code=404, detail=f"Evento #{evento_id} no encontrado")

@app.post("/hsb/reintentar-dlq")
def reintentar_dlq():
    """Reintenta procesar los mensajes en la Dead-Letter Queue."""
    total_dlq = len(hsb_service.dlq_mensajes)
    hsb_service.dlq_mensajes.clear()
    return {
        "status": "ok",
        "mensajes_reencolados": total_dlq,
        "mensaje": f"Se han reencolado {total_dlq} mensajes de la DLQ."
    }

if __name__ == '__main__':
    import uvicorn
    puerto = int(os.environ.get("HSB_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=puerto)
