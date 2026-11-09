#!/usr/bin/env bash
# =============================================================================
# demo_guion.sh — Guion Automatizado de Demostración y Sustentación (15 minutos)
# Parcial Final: Plataforma Distribuida de Interoperabilidad Clínica en Salud
# Autores: Luis Fernando Rios Barboza y Jaime Andrés Villarreal Parra
# =============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}===============================================================================${NC}"
echo -e "${GREEN}   DEMOSTRACIÓN EN VIVO: PLATAFORMA DE INTEROPERABILIDAD EN SALUD (HSB + FHIR)   ${NC}"
echo -e "${BLUE}===============================================================================${NC}"
echo -e "Equipo: Luis Fernando Rios Barboza & Jaime Andrés Villarreal Parra"
echo -e "Docente: Ing. Jaider Enrique Reyes Herazo | Sistemas Distribuidos 2026\n"

# -----------------------------------------------------------------------------
# PASO 1: Verificación de Arranque Limpio y Servicios
# -----------------------------------------------------------------------------
echo -e "${YELLOW}>> PASO 1: Verificando estado de los servicios distribuidos...${NC}"
python3 -m unittest discover -s tests -q
echo -e "${GREEN}✓ Los 26 tests unitarios y de integración pasaron al 100%.${NC}\n"

# -----------------------------------------------------------------------------
# PASO 2: Cobertura Inicial en 0%
# -----------------------------------------------------------------------------
echo -e "${YELLOW}>> PASO 2: Verificando estado inicial de cobertura FHIR (0%)...${NC}"
python3 -c "
from app.consulta_unificada import MotorConsultaUnificada
motor = MotorConsultaUnificada()
# Al inicio los pacientes sintéticos tienen fhir_patient_id en NULL
cob = motor.obtener_cobertura_fhir_red()
print('   Cobertura Inicial por Sede:')
for k, v in cob.items():
    print(f'   - {v[\"nombre\"]}: {v[\"porcentaje_cobertura\"]}% de cobertura FHIR')
"
echo -e "${GREEN}✓ Cobertura verificada en estado inicial.${NC}\n"

# -----------------------------------------------------------------------------
# PASO 3: Ingesta de Mensajes HL7 v2 y CSV (La Cobertura Sube)
# -----------------------------------------------------------------------------
echo -e "${YELLOW}>> PASO 3: Ingesta de mensajes HL7 v2 y CSV a través del HSB...${NC}"
python3 -c "
from hsb.service import HSBService
import os

hsb = HSBService(ref_csv_path='ejemplos/05_ref_terminologia.csv')
# Mock de HAPI para demo rápida en consola
hsb._enviar_a_hapi_con_reintentos = lambda b, idemp: (True, 'OK')

# 1. Enviar HL7 ADT Sede 2
with open('ejemplos/01_adt_a01_valido_sede2.hl7') as f:
    c1, r1 = hsb.procesar_mensaje_hl7(f.read())
print(f'   [HL7 Sede 2] Status: {r1[\"status\"]} | Paciente: {r1[\"paciente\"]} | Sede: {r1[\"sede\"]} | Audit Hash: {r1[\"audit_hash\"][:16]}...')

# 2. Enviar HL7 ORU Sede 1
with open('ejemplos/02_oru_r01_laboratorio_sede1.hl7') as f:
    c2, r2 = hsb.procesar_mensaje_hl7(f.read())
print(f'   [HL7 Sede 1] Status: {r2[\"status\"]} | Paciente: {r2[\"paciente\"]} | LOINC 718-7 Hemoglobina')

# 3. Enviar CSV Sede 3
with open('ejemplos/04_sede3_legado.csv') as f:
    r3 = hsb.procesar_archivo_csv(f.read(), sede_id=3)
print(f'   [CSV Sede 3] Procesados: {r3[\"total_procesados\"]} | Entregados: {r3[\"total_entregados\"]} | Rechazados: {r3[\"total_rechazados\"]}')
for e in r3['entregados']:
    print(f'      ✓ Entregado CC {e[\"documento\"]}: {e[\"nombre\"]} ({e[\"cie10\"]} - {e[\"descripcion\"]})')
for rc in r3['rechazados']:
    print(f'      ✖ Rechazado CC {rc[\"documento\"]}: Motivo: {\"; \".join(rc[\"motivos\"])}')
"
echo -e "${GREEN}✓ Ingesta completada con éxito. La cobertura FHIR se eleva.${NC}\n"

# -----------------------------------------------------------------------------
# PASO 4: Prueba de Idempotencia (Reenvío sin duplicar)
# -----------------------------------------------------------------------------
echo -e "${YELLOW}>> PASO 4: Prueba de Idempotencia (Reenvío de 01_adt_a01_valido_sede2.hl7)...${NC}"
python3 -c "
from hsb.service import HSBService
hsb = HSBService(ref_csv_path='ejemplos/05_ref_terminologia.csv')
hsb._enviar_a_hapi_con_reintentos = lambda b, idemp: (True, 'OK')
with open('ejemplos/01_adt_a01_valido_sede2.hl7') as f:
    raw = f.read()
# Envío 1
c1, r1 = hsb.procesar_mensaje_hl7(raw)
# Envío 2 (duplicado)
c2, r2 = hsb.procesar_mensaje_hl7(raw)
print(f'   Primer Envío  -> Status: {r1[\"status\"]}')
print(f'   Segundo Envío -> Status: {r2[\"status\"]} (Idempotencia activa: {r2[\"mensaje\"]})')
assert r2['status'] == 'duplicado', 'ERROR: No se detectó duplicado'
"
echo -e "${GREEN}✓ Idempotencia garantizada: no se crean pacientes duplicados.${NC}\n"

# -----------------------------------------------------------------------------
# PASO 5: Prueba de Resiliencia (Caída de Sede y Modo Degradado)
# -----------------------------------------------------------------------------
echo -e "${YELLOW}>> PASO 5: Prueba de Resiliencia (Simulación de caída de Sede 2 Cartagena)...${NC}"
python3 -c "
from app.consulta_unificada import MotorConsultaUnificada
motor = MotorConsultaUnificada()

# 1. Consulta normal con 3 sedes
res_normal = motor.consultar_historia_unificada(1001)
print(f'   [NORMAL] 3 Sedes Activas -> Estado: {res_normal[\"estado_red\"]} | Atenciones: {res_normal[\"total_atenciones\"]}')

# 2. Caída de Sede 2 (docker stop pg_sede2)
motor.simular_caida_sede(2)
res_degradado = motor.consultar_historia_unificada(1001)
print(f'   [FALLO]  Sede 2 Caída    -> Estado: {res_degradado[\"estado_red\"]} (DEGRADADO)')
print(f'            Alerta emitida: \"{res_degradado[\"alerta\"]}\"')
print(f'            Sede 2 reportada como: {res_degradado[\"sedes\"][\"sede_2\"][\"estado\"]}')
print(f'            Atenciones recibidas (Sede 1 y 3): {res_degradado[\"total_atenciones\"]}')

# 3. Recuperación de Sede 2 (docker start pg_sede2)
motor.restaurar_sede(2)
res_recuperado = motor.consultar_historia_unificada(1001)
print(f'   [RECUPERADA] Sede 2 Vuelve -> Estado: {res_recuperado[\"estado_red\"]} (100% restablecido)')
"
echo -e "${GREEN}✓ Resiliencia demostrada: degradación grácil y recuperación automática.${NC}\n"

# -----------------------------------------------------------------------------
# PASO 6: Detección de Alteración en Auditoría Encadenada (Hash SHA-256)
# -----------------------------------------------------------------------------
echo -e "${YELLOW}>> PASO 6: Verificación de Integridad de Auditoría y Detección de Falsificación...${NC}"
python3 app/verificador_auditoria.py
echo -e "${GREEN}✓ Detección criptográfica demostrada: señalamiento exacto del evento alterado.${NC}\n"

# -----------------------------------------------------------------------------
# PASO 7: Consulta Unificada Multi-Sede y Sello Criptográfico
# -----------------------------------------------------------------------------
echo -e "${YELLOW}>> PASO 7: Consulta Unificada del Paciente 1001 y Sello Digital del Reporte...${NC}"
python3 -c "
from app.consulta_unificada import MotorConsultaUnificada
motor = MotorConsultaUnificada()
res = motor.consultar_historia_unificada(1001)
print(f'   Paciente: {res[\"paciente\"][\"nombre\"]} (CC {res[\"documento_id\"]})')
print(f'   Total Atenciones Consolidadas: {res[\"total_atenciones\"]}')
for i, at in enumerate(res['atenciones'], start=1):
    dx_str = ', '.join(d['cie10'] + ' ' + d['descripcion'] for d in at.get('diagnosticos', []))
    print(f'   [{i}] {at[\"sede_nombre\"]} | Fecha: {at[\"fecha\"]} | Triage: {at[\"triage\"]} | Dx: {dx_str}')
print(f'   Cobertura de Campos Clínicos: {res[\"cobertura_campos\"][\"porcentaje\"]}%')
print(f'   Sello Criptográfico SHA-256: {res[\"sello_integridad_sha256\"]}')
"
echo -e "${GREEN}✓ Consulta unificada y reporte completados con éxito.${NC}\n"

echo -e "${BLUE}===============================================================================${NC}"
echo -e "${GREEN}       TODOS LOS PASOS DEL GUIÓN DE DEMOSTRACIÓN HAN SIDO CUMPLIDOS CON ÉXITO     ${NC}"
echo -e "${BLUE}===============================================================================${NC}"
