#!/usr/bin/env python3
"""
Genera diagramas vectoriales SVG de alta definición para los 4 diagramas UML y la Arquitectura.
Diseñado para la plantilla v7 y presentación del Parcial Final.
"""

import os

SVG_DIR = os.path.dirname(os.path.abspath(__file__))

def create_svg_casos_de_uso():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 800" width="100%" height="100%" style="background:#f8fafc; font-family:system-ui, -apple-system, sans-serif;">
  <defs>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="2" dy="4" stdDeviation="4" flood-color="#0f172a" flood-opacity="0.08" />
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#64748b"/>
    </marker>
    <marker id="include" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#3b82f6"/>
    </marker>
  </defs>

  <!-- Title -->
  <text x="550" y="40" text-anchor="middle" font-size="22" font-weight="bold" fill="#0f172a">Diagrama de Casos de Uso — Plataforma de Interoperabilidad en Salud</text>
  <text x="550" y="65" text-anchor="middle" font-size="14" fill="#64748b">5 Actores (4 roles + HIS Legado) y 10 Casos de Uso Centrales</text>

  <!-- System Boundary -->
  <rect x="250" y="90" width="600" height="680" rx="16" fill="#ffffff" stroke="#cbd5e1" stroke-width="2" filter="url(#shadow)"/>
  <rect x="250" y="90" width="600" height="40" rx="16" fill="#f1f5f9"/>
  <text x="550" y="116" text-anchor="middle" font-size="15" font-weight="600" fill="#334155">Sistema Central HSB + FHIR R4 + Almacén Distribuido</text>

  <!-- Actors Left: Sistema Sede & Admisionista & Paciente -->
  <!-- Actor 1: Sistema Sede Legada -->
  <g transform="translate(80, 140)">
    <circle cx="50" cy="25" r="16" fill="#e0e7ff" stroke="#4f46e5" stroke-width="2"/>
    <line x1="50" y1="41" x2="50" y2="75" stroke="#4f46e5" stroke-width="2"/>
    <line x1="25" y1="55" x2="75" y2="55" stroke="#4f46e5" stroke-width="2"/>
    <line x1="50" y1="75" x2="30" y2="105" stroke="#4f46e5" stroke-width="2"/>
    <line x1="50" y1="75" x2="70" y2="105" stroke="#4f46e5" stroke-width="2"/>
    <text x="50" y="125" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e1b4b">Sistema Sede</text>
    <text x="50" y="140" text-anchor="middle" font-size="11" fill="#6366f1">(HIS / LIS Legado)</text>
  </g>

  <!-- Actor 2: Admisionista -->
  <g transform="translate(80, 360)">
    <circle cx="50" cy="25" r="16" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
    <line x1="50" y1="41" x2="50" y2="75" stroke="#2563eb" stroke-width="2"/>
    <line x1="25" y1="55" x2="75" y2="55" stroke="#2563eb" stroke-width="2"/>
    <line x1="50" y1="75" x2="30" y2="105" stroke="#2563eb" stroke-width="2"/>
    <line x1="50" y1="75" x2="70" y2="105" stroke="#2563eb" stroke-width="2"/>
    <text x="50" y="125" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e3a8a">Admisionista</text>
    <text x="50" y="140" text-anchor="middle" font-size="11" fill="#3b82f6">(Triage y Admisión)</text>
  </g>

  <!-- Actor 3: Paciente -->
  <g transform="translate(80, 570)">
    <circle cx="50" cy="25" r="16" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
    <line x1="50" y1="41" x2="50" y2="75" stroke="#16a34a" stroke-width="2"/>
    <line x1="25" y1="55" x2="75" y2="55" stroke="#16a34a" stroke-width="2"/>
    <line x1="50" y1="75" x2="30" y2="105" stroke="#16a34a" stroke-width="2"/>
    <line x1="50" y1="75" x2="70" y2="105" stroke="#16a34a" stroke-width="2"/>
    <text x="50" y="125" text-anchor="middle" font-size="13" font-weight="bold" fill="#14532d">Paciente</text>
    <text x="50" y="140" text-anchor="middle" font-size="11" fill="#16a34a">(Titular de HC)</text>
  </g>

  <!-- Actors Right: Médico & Auditor -->
  <!-- Actor 4: Médico -->
  <g transform="translate(930, 240)">
    <circle cx="50" cy="25" r="16" fill="#fef3c7" stroke="#d97706" stroke-width="2"/>
    <line x1="50" y1="41" x2="50" y2="75" stroke="#d97706" stroke-width="2"/>
    <line x1="25" y1="55" x2="75" y2="55" stroke="#d97706" stroke-width="2"/>
    <line x1="50" y1="75" x2="30" y2="105" stroke="#d97706" stroke-width="2"/>
    <line x1="50" y1="75" x2="70" y2="105" stroke="#d97706" stroke-width="2"/>
    <text x="50" y="125" text-anchor="middle" font-size="13" font-weight="bold" fill="#78350f">Médico</text>
    <text x="50" y="140" text-anchor="middle" font-size="11" fill="#d97706">(Atención Clínica)</text>
  </g>

  <!-- Actor 5: Auditor -->
  <g transform="translate(930, 520)">
    <circle cx="50" cy="25" r="16" fill="#f1f5f9" stroke="#475569" stroke-width="2"/>
    <line x1="50" y1="41" x2="50" y2="75" stroke="#475569" stroke-width="2"/>
    <line x1="25" y1="55" x2="75" y2="55" stroke="#475569" stroke-width="2"/>
    <line x1="50" y1="75" x2="30" y2="105" stroke="#475569" stroke-width="2"/>
    <line x1="50" y1="75" x2="70" y2="105" stroke="#475569" stroke-width="2"/>
    <text x="50" y="125" text-anchor="middle" font-size="13" font-weight="bold" fill="#0f172a">Auditor</text>
    <text x="50" y="140" text-anchor="middle" font-size="11" fill="#475569">(Control y Calidad)</text>
  </g>

  <!-- Use Cases inside boundary -->
  <!-- UC1 -->
  <g id="uc1">
    <ellipse cx="430" cy="170" rx="130" ry="25" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="430" y="174" text-anchor="middle" font-size="12" font-weight="500" fill="#1e40af">CU1: Ingerir mensaje HL7 v2 / CSV</text>
  </g>

  <!-- UC2 -->
  <g id="uc2">
    <ellipse cx="680" cy="170" rx="130" ry="25" fill="#f0fdf4" stroke="#22c55e" stroke-width="1.5"/>
    <text x="680" y="174" text-anchor="middle" font-size="12" font-weight="500" fill="#15803d">CU2: Validar y normalizar a FHIR R4</text>
  </g>

  <!-- UC3 -->
  <g id="uc3">
    <ellipse cx="550" cy="240" rx="140" ry="25" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="550" y="244" text-anchor="middle" font-size="12" font-weight="500" fill="#1e40af">CU3: Enrutar y persistir en nodo de sede</text>
  </g>

  <!-- UC4 -->
  <g id="uc4">
    <ellipse cx="550" cy="310" rx="150" ry="25" fill="#fef2f2" stroke="#ef4444" stroke-width="1.5"/>
    <text x="550" y="314" text-anchor="middle" font-size="12" font-weight="bold" fill="#b91c1c">CU4: Consultar HC unificada multi-sede</text>
  </g>

  <!-- UC5 -->
  <g id="uc5">
    <ellipse cx="430" cy="390" rx="130" ry="25" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="430" y="394" text-anchor="middle" font-size="12" font-weight="500" fill="#1e40af">CU5: Registrar admisión y triage</text>
  </g>

  <!-- UC6 -->
  <g id="uc6">
    <ellipse cx="680" cy="390" rx="140" ry="25" fill="#fffbeb" stroke="#f59e0b" stroke-width="1.5"/>
    <text x="680" y="394" text-anchor="middle" font-size="12" font-weight="500" fill="#b45309">CU6: Registrar diagnóstico CIE-10</text>
  </g>

  <!-- UC7 -->
  <g id="uc7">
    <ellipse cx="680" cy="460" rx="140" ry="25" fill="#fffbeb" stroke="#f59e0b" stroke-width="1.5"/>
    <text x="680" y="464" text-anchor="middle" font-size="12" font-weight="500" fill="#b45309">CU7: Formular tecnologías y egreso</text>
  </g>

  <!-- UC8 -->
  <g id="uc8">
    <ellipse cx="430" cy="460" rx="130" ry="25" fill="#f8fafc" stroke="#64748b" stroke-width="1.5"/>
    <text x="430" y="464" text-anchor="middle" font-size="12" font-weight="500" fill="#334155">CU8: Monitorear estado de mensajes HSB</text>
  </g>

  <!-- UC9 -->
  <g id="uc9">
    <ellipse cx="430" cy="540" rx="130" ry="25" fill="#f0fdf4" stroke="#22c55e" stroke-width="1.5"/>
    <text x="430" y="544" text-anchor="middle" font-size="12" font-weight="500" fill="#15803d">CU9: Descargar Bundle FHIR R4</text>
  </g>

  <!-- UC10 -->
  <g id="uc10">
    <ellipse cx="430" cy="620" rx="130" ry="25" fill="#f0fdf4" stroke="#22c55e" stroke-width="1.5"/>
    <text x="430" y="624" text-anchor="middle" font-size="12" font-weight="500" fill="#15803d">CU10: Consultar accesos a su historia</text>
  </g>

  <!-- UC11 -->
  <g id="uc11">
    <ellipse cx="680" cy="620" rx="140" ry="25" fill="#f1f5f9" stroke="#475569" stroke-width="1.5"/>
    <text x="680" y="624" text-anchor="middle" font-size="12" font-weight="500" fill="#0f172a">CU11: Verificar auditoría encadenada</text>
  </g>

  <!-- UC12 -->
  <g id="uc12">
    <ellipse cx="550" cy="700" rx="140" ry="25" fill="#f8fafc" stroke="#475569" stroke-width="1.5"/>
    <text x="550" y="704" text-anchor="middle" font-size="12" font-weight="500" fill="#0f172a">CU12: Tablero de métricas y cobertura</text>
  </g>

  <!-- Connectors -->
  <!-- HIS -> UC1 -->
  <line x1="170" y1="180" x2="300" y2="170" stroke="#64748b" stroke-width="1.5"/>
  <!-- UC1 ..> UC2 include -->
  <line x1="560" y1="170" x2="550" y2="170" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#include)"/>
  <!-- UC2 ..> UC3 include -->
  <path d="M 680 195 L 680 240 L 690 240" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="4,3"/>

  <!-- Admisionista -> UC5 & UC8 & UC4 -->
  <line x1="170" y1="410" x2="300" y2="390" stroke="#64748b" stroke-width="1.5"/>
  <line x1="170" y1="415" x2="300" y2="460" stroke="#64748b" stroke-width="1.5"/>

  <!-- Paciente -> UC4 & UC9 & UC10 -->
  <line x1="170" y1="620" x2="300" y2="540" stroke="#64748b" stroke-width="1.5"/>
  <line x1="170" y1="630" x2="300" y2="620" stroke="#64748b" stroke-width="1.5"/>
  <path d="M 170 610 Q 220 400 400 320" stroke="#64748b" stroke-width="1.5" fill="none"/>

  <!-- Medico -> UC4 & UC6 & UC7 -->
  <line x1="930" y1="290" x2="700" y2="310" stroke="#64748b" stroke-width="1.5"/>
  <line x1="930" y1="300" x2="820" y2="390" stroke="#64748b" stroke-width="1.5"/>
  <line x1="930" y1="310" x2="820" y2="460" stroke="#64748b" stroke-width="1.5"/>

  <!-- Auditor -> UC4 & UC11 & UC12 -->
  <path d="M 930 560 Q 860 360 700 320" stroke="#64748b" stroke-width="1.5" fill="none"/>
  <line x1="930" y1="580" x2="820" y2="620" stroke="#64748b" stroke-width="1.5"/>
  <line x1="930" y1="590" x2="690" y2="700" stroke="#64748b" stroke-width="1.5"/>
</svg>'''
    return svg

def create_svg_secuencia():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1150 780" width="100%" height="100%" style="background:#ffffff; font-family:system-ui, -apple-system, sans-serif;">
  <defs>
    <filter id="box-shadow" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="1" dy="3" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563eb"/>
    </marker>
    <marker id="arrow-ret" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#64748b"/>
    </marker>
    <marker id="arrow-err" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#dc2626"/>
    </marker>
  </defs>

  <!-- Title -->
  <text x="575" y="35" text-anchor="middle" font-size="20" font-weight="bold" fill="#0f172a">Diagrama de Secuencia — Ingesta, Validación, Idempotencia y Publicación FHIR</text>
  <text x="575" y="58" text-anchor="middle" font-size="13" fill="#64748b">Flujo de Extremo a Extremo con Caminos de Rechazo, Duplicado y Entrega Exitosa</text>

  <!-- Lifeline Boxes -->
  <!-- Col 1: HIS Sede -->
  <g transform="translate(60, 80)">
    <rect x="0" y="0" width="120" height="40" rx="8" fill="#e0e7ff" stroke="#4338ca" stroke-width="1.5" filter="url(#box-shadow)"/>
    <text x="60" y="24" text-anchor="middle" font-size="13" font-weight="bold" fill="#312e81">HIS Sede 2</text>
    <line x1="60" y1="40" x2="60" y2="700" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5"/>
  </g>

  <!-- Col 2: HSB API -->
  <g transform="translate(240, 80)">
    <rect x="0" y="0" width="130" height="40" rx="8" fill="#dbeafe" stroke="#1d4ed8" stroke-width="1.5" filter="url(#box-shadow)"/>
    <text x="65" y="24" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e3a8a">HSB (FastAPI)</text>
    <line x1="65" y1="40" x2="65" y2="700" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5"/>
  </g>

  <!-- Col 3: Validador & Idempotencia -->
  <g transform="translate(430, 80)">
    <rect x="0" y="0" width="150" height="40" rx="8" fill="#f1f5f9" stroke="#475569" stroke-width="1.5" filter="url(#box-shadow)"/>
    <text x="75" y="24" text-anchor="middle" font-size="13" font-weight="bold" fill="#0f172a">Validador / Idemp</text>
    <line x1="75" y1="40" x2="75" y2="700" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5"/>
  </g>

  <!-- Col 4: Normalizador FHIR -->
  <g transform="translate(640, 80)">
    <rect x="0" y="0" width="140" height="40" rx="8" fill="#dcfce7" stroke="#15803d" stroke-width="1.5" filter="url(#box-shadow)"/>
    <text x="70" y="24" text-anchor="middle" font-size="13" font-weight="bold" fill="#14532d">Normalizador FHIR</text>
    <line x1="70" y1="40" x2="70" y2="700" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5"/>
  </g>

  <!-- Col 5: HAPI FHIR Server -->
  <g transform="translate(830, 80)">
    <rect x="0" y="0" width="130" height="40" rx="8" fill="#ffedd5" stroke="#c2410c" stroke-width="1.5" filter="url(#box-shadow)"/>
    <text x="65" y="24" text-anchor="middle" font-size="13" font-weight="bold" fill="#7c2d12">HAPI FHIR R4</text>
    <line x1="65" y1="40" x2="65" y2="700" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5"/>
  </g>

  <!-- Col 6: DB Sede & Auditoría -->
  <g transform="translate(990, 80)">
    <rect x="0" y="0" width="130" height="40" rx="8" fill="#f5f3ff" stroke="#6d28d9" stroke-width="1.5" filter="url(#box-shadow)"/>
    <text x="65" y="24" text-anchor="middle" font-size="13" font-weight="bold" fill="#4c1d95">pg_sede / Auditoría</text>
    <line x1="65" y1="40" x2="65" y2="700" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5"/>
  </g>

  <!-- Steps -->
  <!-- 1. POST HL7 -->
  <line x1="120" y1="150" x2="300" y2="150" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="210" y="142" text-anchor="middle" font-size="12" font-weight="500" fill="#1e3a8a">1. POST /hsb/hl7 (ADT^A01)</text>

  <!-- 2. Check Idempotency -->
  <line x1="305" y1="180" x2="500" y2="180" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="402" y="172" text-anchor="middle" font-size="12" fill="#334155">2. Verificar clave idempotencia (MSH-10)</text>

  <!-- Frame ALT 1: Duplicado -->
  <rect x="80" y="200" width="460" height="70" rx="6" fill="#f8fafc" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,4"/>
  <text x="90" y="218" font-size="11" font-weight="bold" fill="#64748b">[alt: Clave ya procesada (Duplicado)]</text>
  <line x1="500" y1="240" x2="310" y2="240" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#arrow-ret)"/>
  <line x1="300" y1="255" x2="125" y2="255" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#arrow-ret)"/>
  <text x="210" y="250" text-anchor="middle" font-size="11" fill="#475569">200 OK {"status": "duplicado"}</text>

  <!-- 3. Validate Rules -->
  <line x1="505" y1="290" x2="535" y2="290" stroke="#2563eb" stroke-width="1.5"/>
  <line x1="535" y1="290" x2="535" y2="310" stroke="#2563eb" stroke-width="1.5"/>
  <line x1="535" y1="310" x2="505" y2="310" stroke="#2563eb" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="560" y="304" font-size="11" fill="#1e3a8a">3. Validar: doc numérico, sexo M/F, CIE-10</text>

  <!-- Frame ALT 2: Rechazado -->
  <rect x="80" y="330" width="980" height="70" rx="6" fill="#fef2f2" stroke="#f87171" stroke-width="1" stroke-dasharray="4,4"/>
  <text x="90" y="348" font-size="11" font-weight="bold" fill="#dc2626">[alt: Validación Fallida (3 motivos de rechazo)]</text>
  <line x1="505" y1="370" x2="1050" y2="370" stroke="#dc2626" stroke-width="1.5" marker-end="url(#arrow-err)"/>
  <text x="770" y="364" text-anchor="middle" font-size="11" fill="#b91c1c">Registrar mensaje RECHAZADO y evento auditoría</text>
  <line x1="300" y1="385" x2="125" y2="385" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#arrow-err)"/>
  <text x="210" y="380" text-anchor="middle" font-size="11" fill="#b91c1c">400 Bad Request {"motivos": [...]}</text>

  <!-- 4. Transform FHIR -->
  <line x1="505" y1="420" x2="705" y2="420" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="605" y="412" text-anchor="middle" font-size="12" fill="#15803d">4. Transformar a Bundle transaction</text>

  <line x1="710" y1="450" x2="310" y2="450" stroke="#15803d" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrow-ret)"/>
  <text x="510" y="444" text-anchor="middle" font-size="11" fill="#15803d">Bundle R4 (Patient/pac-1007, Encounter, Condition J45.9)</text>

  <!-- 5. PUT to HAPI FHIR -->
  <line x1="310" y1="480" x2="890" y2="480" stroke="#c2410c" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="600" y="474" text-anchor="middle" font-size="12" fill="#c2410c">5. PUT /Bundle (Transaction determinista en HAPI)</text>

  <line x1="890" y1="510" x2="310" y2="510" stroke="#c2410c" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrow-ret)"/>
  <text x="600" y="504" text-anchor="middle" font-size="11" fill="#7c2d12">200 OK (Recursos creados / actualizados en FHIR)</text>

  <!-- 6. Persist to Node Sede -->
  <line x1="310" y1="540" x2="1050" y2="540" stroke="#4c1d95" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="680" y="534" text-anchor="middle" font-size="12" fill="#4c1d95">6. INSERT usuario, atencion, diagnostico en pg_sede2</text>

  <!-- 7. Hash chained audit log -->
  <line x1="310" y1="570" x2="1050" y2="570" stroke="#4c1d95" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="680" y="564" text-anchor="middle" font-size="12" fill="#4c1d95">7. INSERT evento_auditoria (hash = SHA-256(prev_hash + evento))</text>

  <line x1="1050" y1="600" x2="310" y2="600" stroke="#4c1d95" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrow-ret)"/>
  <text x="680" y="594" text-anchor="middle" font-size="11" fill="#4c1d95">Confirmación de persistencia y Hash Encadenado</text>

  <!-- 8. Return response -->
  <line x1="300" y1="640" x2="125" y2="640" stroke="#15803d" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="210" y="632" text-anchor="middle" font-size="12" font-weight="bold" fill="#15803d">8. 200 OK {"status": "entregado", "audit_hash": "..."}</text>

  <!-- Note on Retry/Fault Tolerance -->
  <rect x="250" y="670" width="670" height="50" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
  <text x="585" y="692" text-anchor="middle" font-size="11" fill="#475569">Manejo de Fallas Parciales: Si HAPI o el nodo caen, el mensaje pasa a REINTENTANDO</text>
  <text x="585" y="708" text-anchor="middle" font-size="11" fill="#64748b">con retroceso exponencial (1s, 2s, 4s...) hasta 4 intentos antes de pasar a la DLQ (MUERTO).</text>
</svg>'''
    return svg

def create_svg_clases():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 860" width="100%" height="100%" style="background:#f8fafc; font-family:system-ui, -apple-system, sans-serif;">
  <defs>
    <filter id="cshadow" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="2" dy="4" stdDeviation="4" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
  </defs>

  <!-- Title -->
  <text x="600" y="38" text-anchor="middle" font-size="22" font-weight="bold" fill="#0f172a">Diagrama de Clases — Modelo de Entidades y Servicios Distribuidos</text>
  <text x="600" y="62" text-anchor="middle" font-size="14" fill="#64748b">11 Clases: Esquema Clínico, Bus de Integración, Trazabilidad Inmutable y FHIR R4</text>

  <!-- Row 1: Usuario, Atencion, Diagnostico -->
  <!-- Class: Usuario -->
  <g transform="translate(50, 90)">
    <rect x="0" y="0" width="230" height="210" rx="8" fill="#ffffff" stroke="#3b82f6" stroke-width="2" filter="url(#cshadow)"/>
    <rect x="0" y="0" width="230" height="32" rx="8" fill="#eff6ff"/>
    <text x="115" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e40af">Usuario (Paciente)</text>
    <text x="15" y="52" font-size="11" fill="#334155">+ documento_id: BigInt [PK]</text>
    <text x="15" y="70" font-size="11" fill="#334155">+ tipo_documento: String</text>
    <text x="15" y="88" font-size="11" fill="#334155">+ nombre_completo: String</text>
    <text x="15" y="106" font-size="11" fill="#334155">+ fecha_nacimiento: Date</text>
    <text x="15" y="124" font-size="11" fill="#334155">+ sexo: String (M, F, O)</text>
    <text x="15" y="142" font-size="11" fill="#334155">+ fhir_patient_id: String</text>
    <text x="15" y="160" font-size="11" fill="#334155">+ created_at: DateTime</text>
    <text x="15" y="178" font-size="11" fill="#334155">+ updated_at: DateTime</text>
    <line x1="0" y1="190" x2="230" y2="190" stroke="#e2e8f0"/>
    <text x="15" y="204" font-size="10" fill="#64748b">+ calcular_cobertura_fhir()</text>
  </g>

  <!-- Class: Atencion -->
  <g transform="translate(340, 90)">
    <rect x="0" y="0" width="240" height="210" rx="8" fill="#ffffff" stroke="#3b82f6" stroke-width="2" filter="url(#cshadow)"/>
    <rect x="0" y="0" width="240" height="32" rx="8" fill="#eff6ff"/>
    <text x="120" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e40af">Atencion (Encounter)</text>
    <text x="15" y="52" font-size="11" fill="#334155">+ atencion_id: Integer [PK]</text>
    <text x="15" y="70" font-size="11" fill="#334155">+ documento_id: BigInt [FK]</text>
    <text x="15" y="88" font-size="11" fill="#334155">+ entidad_salud: String (Sede)</text>
    <text x="15" y="106" font-size="11" fill="#334155">+ fecha_ingreso: DateTime</text>
    <text x="15" y="124" font-size="11" fill="#334155">+ modalidad_entrega: String</text>
    <text x="15" y="142" font-size="11" fill="#334155">+ clasificacion_triage: String (1-5)</text>
    <text x="15" y="160" font-size="11" fill="#334155">+ causa_atencion: Text</text>
    <text x="15" y="178" font-size="11" fill="#334155">+ profesional_id: String [FK]</text>
    <line x1="0" y1="190" x2="240" y2="190" stroke="#e2e8f0"/>
    <text x="15" y="204" font-size="10" fill="#64748b">+ exportar_fhir_encounter()</text>
  </g>

  <!-- Class: Diagnostico -->
  <g transform="translate(640, 90)">
    <rect x="0" y="0" width="230" height="180" rx="8" fill="#ffffff" stroke="#f59e0b" stroke-width="2" filter="url(#cshadow)"/>
    <rect x="0" y="0" width="230" height="32" rx="8" fill="#fffbeb"/>
    <text x="115" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#b45309">Diagnostico (Condition)</text>
    <text x="15" y="52" font-size="11" fill="#334155">+ diagnostico_id: Integer [PK]</text>
    <text x="15" y="70" font-size="11" fill="#334155">+ atencion_id: Integer [FK]</text>
    <text x="15" y="88" font-size="11" fill="#334155">+ cie10: String (ej: J45.9)</text>
    <text x="15" y="106" font-size="11" fill="#334155">+ descripcion: String</text>
    <text x="15" y="124" font-size="11" fill="#334155">+ tipo_diagnostico: String</text>
    <text x="15" y="142" font-size="11" fill="#334155">+ fecha_diagnostico: DateTime</text>
    <line x1="0" y1="158" x2="230" y2="158" stroke="#e2e8f0"/>
    <text x="15" y="172" font-size="10" fill="#64748b">+ exportar_fhir_condition()</text>
  </g>

  <!-- Class: TecnologiaSalud -->
  <g transform="translate(930, 90)">
    <rect x="0" y="0" width="220" height="180" rx="8" fill="#ffffff" stroke="#10b981" stroke-width="2" filter="url(#cshadow)"/>
    <rect x="0" y="0" width="220" height="32" rx="8" fill="#ecfdf5"/>
    <text x="110" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#047857">TecnologiaSalud</text>
    <text x="15" y="52" font-size="11" fill="#334155">+ tecnologia_id: UUID [PK]</text>
    <text x="15" y="70" font-size="11" fill="#334155">+ atencion_id: Integer [FK]</text>
    <text x="15" y="88" font-size="11" fill="#334155">+ codigo_tecnologia: String</text>
    <text x="15" y="106" font-size="11" fill="#334155">+ descripcion: String</text>
    <text x="15" y="124" font-size="11" fill="#334155">+ valor_resultado: Float</text>
    <text x="15" y="142" font-size="11" fill="#334155">+ unidad_medida: String</text>
    <line x1="0" y1="158" x2="220" y2="158" stroke="#e2e8f0"/>
    <text x="15" y="172" font-size="10" fill="#64748b">+ exportar_fhir_observation()</text>
  </g>

  <!-- Row 2: Egreso, ProfesionalSalud, RefTerminologia, SedeConfig -->
  <!-- Class: Egreso -->
  <g transform="translate(340, 350)">
    <rect x="0" y="0" width="240" height="140" rx="8" fill="#ffffff" stroke="#3b82f6" stroke-width="2" filter="url(#cshadow)"/>
    <rect x="0" y="0" width="240" height="32" rx="8" fill="#eff6ff"/>
    <text x="120" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e40af">Egreso Clinico</text>
    <text x="15" y="52" font-size="11" fill="#334155">+ egreso_id: Integer [PK]</text>
    <text x="15" y="70" font-size="11" fill="#334155">+ atencion_id: Integer [FK]</text>
    <text x="15" y="88" font-size="11" fill="#334155">+ fecha_egreso: DateTime</text>
    <text x="15" y="106" font-size="11" fill="#334155">+ destino_egreso: String</text>
    <text x="15" y="124" font-size="11" fill="#334155">+ diagnostico_muerte: String</text>
  </g>

  <!-- Class: ProfesionalSalud -->
  <g transform="translate(50, 350)">
    <rect x="0" y="0" width="230" height="140" rx="8" fill="#ffffff" stroke="#64748b" stroke-width="2" filter="url(#cshadow)"/>
    <rect x="0" y="0" width="230" height="32" rx="8" fill="#f8fafc"/>
    <text x="115" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">ProfesionalSalud</text>
    <text x="15" y="52" font-size="11" fill="#334155">+ profesional_id: String [PK]</text>
    <text x="15" y="70" font-size="11" fill="#334155">+ nombre_completo: String</text>
    <text x="15" y="88" font-size="11" fill="#334155">+ registro_medico: String</text>
    <text x="15" y="106" font-size="11" fill="#334155">+ especialidad: String</text>
    <text x="15" y="124" font-size="11" fill="#334155">+ sede_asignada: Integer</text>
  </g>

  <!-- Class: RefTerminologia -->
  <g transform="translate(640, 350)">
    <rect x="0" y="0" width="230" height="140" rx="8" fill="#ffffff" stroke="#8b5cf6" stroke-width="2" filter="url(#cshadow)"/>
    <rect x="0" y="0" width="230" height="32" rx="8" fill="#f5f3ff"/>
    <text x="115" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#6d28d9">RefTerminologia</text>
    <text x="15" y="52" font-size="11" fill="#334155">+ dx_local: String [PK]</text>
    <text x="15" y="70" font-size="11" fill="#334155">+ cie10: String</text>
    <text x="15" y="88" font-size="11" fill="#334155">+ loinc: String</text>
    <text x="15" y="106" font-size="11" fill="#334155">+ descripcion: String</text>
    <line x1="0" y1="118" x2="230" y2="118" stroke="#e2e8f0"/>
    <text x="15" y="132" font-size="10" fill="#64748b">+ mapear_a_estandar(texto)</text>
  </g>

  <!-- Class: SedeConfig -->
  <g transform="translate(930, 350)">
    <rect x="0" y="0" width="220" height="140" rx="8" fill="#ffffff" stroke="#64748b" stroke-width="2" filter="url(#cshadow)"/>
    <rect x="0" y="0" width="220" height="32" rx="8" fill="#f8fafc"/>
    <text x="110" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">SedeConfig (Nodo)</text>
    <text x="15" y="52" font-size="11" fill="#334155">+ sede_id: Integer [PK]</text>
    <text x="15" y="70" font-size="11" fill="#334155">+ nombre: String (Sincelejo/..)</text>
    <text x="15" y="88" font-size="11" fill="#334155">+ host_db: String</text>
    <text x="15" y="106" font-size="11" fill="#334155">+ puerto_db: Integer</text>
    <text x="15" y="124" font-size="11" fill="#334155">+ disponible: Boolean</text>
  </g>

  <!-- Row 3: MensajeBus, EventoAuditoria, FhirBundle -->
  <!-- Class: MensajeBus -->
  <g transform="translate(50, 540)">
    <rect x="0" y="0" width="310" height="250" rx="8" fill="#ffffff" stroke="#ec4899" stroke-width="2" filter="url(#cshadow)"/>
    <rect x="0" y="0" width="310" height="32" rx="8" fill="#fdf2f8"/>
    <text x="155" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#be185d">MensajeBus (HSB)</text>
    <text x="15" y="52" font-size="11" fill="#334155">+ mensaje_id: UUID [PK]</text>
    <text x="15" y="70" font-size="11" fill="#334155">+ clave_idempotencia: String (MSH-10 / Hash)</text>
    <text x="15" y="88" font-size="11" fill="#334155">+ formato_origen: String (HL7_ADT, HL7_ORU, CSV)</text>
    <text x="15" y="106" font-size="11" fill="#334155">+ sede_origen: Integer (1, 2, 3)</text>
    <text x="15" y="124" font-size="11" fill="#334155">+ contenido_raw: Text</text>
    <text x="15" y="142" font-size="11" fill="#334155">+ estado: String (recibido/entregado/rechazado..)</text>
    <text x="15" y="160" font-size="11" fill="#334155">+ intentos_reintento: Integer</text>
    <text x="15" y="178" font-size="11" fill="#334155">+ motivo_rechazo: Text</text>
    <text x="15" y="196" font-size="11" fill="#334155">+ fhir_bundle_id: String</text>
    <text x="15" y="214" font-size="11" fill="#334155">+ created_at: DateTime</text>
    <line x1="0" y1="226" x2="310" y2="226" stroke="#e2e8f0"/>
    <text x="15" y="240" font-size="10" fill="#64748b">+ reencolar_dlq() | + validar_reglas()</text>
  </g>

  <!-- Class: EventoAuditoria -->
  <g transform="translate(410, 540)">
    <rect x="0" y="0" width="370" height="250" rx="8" fill="#ffffff" stroke="#059669" stroke-width="2" filter="url(#cshadow)"/>
    <rect x="0" y="0" width="370" height="32" rx="8" fill="#ecfdf5"/>
    <text x="185" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#047857">EventoAuditoria (Hash-Chained Log)</text>
    <text x="15" y="52" font-size="11" fill="#334155">+ evento_id: Integer [PK, Autoincrement]</text>
    <text x="15" y="70" font-size="11" fill="#334155">+ prev_hash: String (SHA-256 del evento anterior)</text>
    <text x="15" y="88" font-size="11" fill="#334155">+ hash: String (SHA-256(prev_hash + contenido))</text>
    <text x="15" y="106" font-size="11" fill="#334155">+ timestamp: DateTime</text>
    <text x="15" y="124" font-size="11" fill="#334155">+ actor: String (Documento / Usuario)</text>
    <text x="15" y="142" font-size="11" fill="#334155">+ rol: String (paciente, admisionista, medico, auditor)</text>
    <text x="15" y="160" font-size="11" fill="#334155">+ accion: String (LOGIN, CONSULTA_HC, ENVIO_BUS..)</text>
    <text x="15" y="178" font-size="11" fill="#334155">+ sede_id: Integer</text>
    <text x="15" y="196" font-size="11" fill="#334155">+ detalle: Text</text>
    <text x="15" y="214" font-size="11" fill="#334155">+ resultado: String (EXITOSO, DENEGADO, RECHAZADO)</text>
    <line x1="0" y1="226" x2="370" y2="226" stroke="#e2e8f0"/>
    <text x="15" y="240" font-size="10" fill="#64748b">+ calcular_hash() | + verificar_integridad_cadena()</text>
  </g>

  <!-- Class: FhirBundle -->
  <g transform="translate(830, 540)">
    <rect x="0" y="0" width="320" height="250" rx="8" fill="#ffffff" stroke="#c2410c" stroke-width="2" filter="url(#cshadow)"/>
    <rect x="0" y="0" width="320" height="32" rx="8" fill="#fff7ed"/>
    <text x="160" y="22" text-anchor="middle" font-size="14" font-weight="bold" fill="#9a3412">FhirBundle (FHIR R4 Model)</text>
    <text x="15" y="52" font-size="11" fill="#334155">+ resourceType: String = 'Bundle'</text>
    <text x="15" y="70" font-size="11" fill="#334155">+ type: String = 'transaction'</text>
    <text x="15" y="88" font-size="11" fill="#334155">+ patient_entry: Patient (doc, name, birth, gender)</text>
    <text x="15" y="106" font-size="11" fill="#334155">+ encounter_entry: Encounter (class, period, org)</text>
    <text x="15" y="124" font-size="11" fill="#334155">+ condition_entries: List&lt;Condition&gt; (CIE-10)</text>
    <text x="15" y="142" font-size="11" fill="#334155">+ observation_entries: List&lt;Observation&gt; (LOINC)</text>
    <text x="15" y="160" font-size="11" fill="#334155">+ fhir_version: String = '4.0.1'</text>
    <text x="15" y="178" font-size="11" fill="#334155">+ id_determinista: Boolean = True (pac-&lt;doc&gt;)</text>
    <text x="15" y="196" font-size="11" fill="#334155">+ validado_hapi: Boolean</text>
    <line x1="0" y1="226" x2="320" y2="226" stroke="#e2e8f0"/>
    <text x="15" y="240" font-size="10" fill="#64748b">+ to_json() | + enviar_hapi_put()</text>
  </g>

  <!-- Association Lines -->
  <!-- Usuario to Atencion -->
  <line x1="280" y1="190" x2="340" y2="190" stroke="#3b82f6" stroke-width="2"/>
  <text x="310" y="180" text-anchor="middle" font-size="10" fill="#1e40af">1..*</text>

  <!-- Atencion to Diagnostico -->
  <line x1="580" y1="170" x2="640" y2="170" stroke="#f59e0b" stroke-width="2"/>
  <text x="610" y="160" text-anchor="middle" font-size="10" fill="#b45309">0..*</text>

  <!-- Atencion to TecnologiaSalud -->
  <path d="M 580 140 L 930 140" stroke="#10b981" stroke-width="1.5" stroke-dasharray="3,3"/>
  <text x="750" y="132" text-anchor="middle" font-size="10" fill="#047857">0..*</text>

  <!-- Atencion to Egreso -->
  <line x1="460" y1="300" x2="460" y2="350" stroke="#3b82f6" stroke-width="2"/>
  <text x="475" y="330" font-size="10" fill="#1e40af">0..1</text>
</svg>'''
    return svg

def create_svg_estados():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1150 680" width="100%" height="100%" style="background:#f8fafc; font-family:system-ui, -apple-system, sans-serif;">
  <defs>
    <filter id="eshadow" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="2" dy="4" stdDeviation="4" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    <marker id="earrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569"/>
    </marker>
    <marker id="earrow-err" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#dc2626"/>
    </marker>
    <marker id="earrow-ok" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#16a34a"/>
    </marker>
  </defs>

  <!-- Title -->
  <text x="575" y="40" text-anchor="middle" font-size="22" font-weight="bold" fill="#0f172a">Diagrama de Estados — Ciclo de Vida del Mensaje en el HSB</text>
  <text x="575" y="65" text-anchor="middle" font-size="14" fill="#64748b">Transiciones, Validación, Idempotencia, Reintentos Exponenciales y Cola de Mensajes Muertos (DLQ)</text>

  <!-- Start State -->
  <circle cx="80" cy="200" r="16" fill="#0f172a"/>
  <line x1="96" y1="200" x2="160" y2="200" stroke="#475569" stroke-width="2" marker-end="url(#earrow)"/>
  <text x="125" y="190" text-anchor="middle" font-size="11" fill="#475569">POST HTTP</text>

  <!-- State 1: RECIBIDO -->
  <g transform="translate(160, 155)">
    <rect x="0" y="0" width="180" height="90" rx="12" fill="#ffffff" stroke="#3b82f6" stroke-width="2" filter="url(#eshadow)"/>
    <rect x="0" y="0" width="180" height="28" rx="12" fill="#eff6ff"/>
    <text x="90" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e40af">RECIBIDO</text>
    <text x="15" y="48" font-size="11" fill="#334155">• Ingesta HL7 v2 / CSV</text>
    <text x="15" y="66" font-size="11" fill="#334155">• Extracción MSH-10/Hash</text>
    <text x="15" y="82" font-size="10" fill="#64748b">entry: Registrar en DB</text>
  </g>

  <!-- State: DUPLICADO -->
  <g transform="translate(160, 360)">
    <rect x="0" y="0" width="180" height="80" rx="12" fill="#f8fafc" stroke="#94a3b8" stroke-width="2" filter="url(#eshadow)"/>
    <rect x="0" y="0" width="180" height="28" rx="12" fill="#f1f5f9"/>
    <text x="90" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#475569">DUPLICADO</text>
    <text x="15" y="48" font-size="11" fill="#334155">• Idempotencia activa</text>
    <text x="15" y="66" font-size="11" fill="#334155">• Respuesta 200 sin re-insert</text>
  </g>
  <!-- Final state duplicate -->
  <circle cx="250" cy="500" r="16" fill="none" stroke="#64748b" stroke-width="2"/>
  <circle cx="250" cy="500" r="10" fill="#64748b"/>
  <line x1="250" y1="245" x2="250" y2="360" stroke="#475569" stroke-width="2" marker-end="url(#earrow)"/>
  <text x="255" y="300" font-size="11" fill="#64748b">Clave ya existe</text>
  <line x1="250" y1="440" x2="250" y2="484" stroke="#475569" stroke-width="2" marker-end="url(#earrow)"/>

  <!-- Transition RECIBIDO -> VALIDANDO -->
  <line x1="340" y1="200" x2="420" y2="200" stroke="#475569" stroke-width="2" marker-end="url(#earrow)"/>
  <text x="380" y="190" text-anchor="middle" font-size="11" fill="#475569">Clave nueva</text>

  <!-- State 2: VALIDANDO -->
  <g transform="translate(420, 155)">
    <rect x="0" y="0" width="190" height="90" rx="12" fill="#ffffff" stroke="#f59e0b" stroke-width="2" filter="url(#eshadow)"/>
    <rect x="0" y="0" width="190" height="28" rx="12" fill="#fffbeb"/>
    <text x="95" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#b45309">VALIDANDO</text>
    <text x="15" y="48" font-size="11" fill="#334155">• Documento 4-15 dígitos</text>
    <text x="15" y="66" font-size="11" fill="#334155">• Sexo admitido (M, F, O)</text>
    <text x="15" y="82" font-size="10" fill="#64748b">• Diagnóstico en CIE-10</text>
  </g>

  <!-- State: RECHAZADO -->
  <g transform="translate(420, 360)">
    <rect x="0" y="0" width="190" height="80" rx="12" fill="#fef2f2" stroke="#ef4444" stroke-width="2" filter="url(#eshadow)"/>
    <rect x="0" y="0" width="190" height="28" rx="12" fill="#fee2e2"/>
    <text x="95" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#b91c1c">RECHAZADO</text>
    <text x="15" y="48" font-size="11" fill="#991b1b">• Guarda lista de motivos</text>
    <text x="15" y="66" font-size="11" fill="#991b1b">• Auditoría registra evento</text>
  </g>
  <!-- Final state rechazado -->
  <circle cx="515" cy="500" r="16" fill="none" stroke="#dc2626" stroke-width="2"/>
  <circle cx="515" cy="500" r="10" fill="#dc2626"/>
  <line x1="515" y1="245" x2="515" y2="360" stroke="#dc2626" stroke-width="2" marker-end="url(#earrow-err)"/>
  <text x="525" y="300" font-size="11" fill="#dc2626">Falla validación</text>
  <line x1="515" y1="440" x2="515" y2="484" stroke="#dc2626" stroke-width="2" marker-end="url(#earrow-err)"/>

  <!-- Transition VALIDANDO -> TRANSFORMADO -->
  <line x1="610" y1="200" x2="690" y2="200" stroke="#16a34a" stroke-width="2" marker-end="url(#earrow-ok)"/>
  <text x="650" y="190" text-anchor="middle" font-size="11" fill="#16a34a">Válido</text>

  <!-- State 3: TRANSFORMADO -->
  <g transform="translate(690, 155)">
    <rect x="0" y="0" width="190" height="90" rx="12" fill="#ffffff" stroke="#10b981" stroke-width="2" filter="url(#eshadow)"/>
    <rect x="0" y="0" width="190" height="28" rx="12" fill="#ecfdf5"/>
    <text x="95" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#047857">TRANSFORMADO</text>
    <text x="15" y="48" font-size="11" fill="#334155">• Construye Bundle R4</text>
    <text x="15" y="66" font-size="11" fill="#334155">• IDs fijos: pac-&lt;doc&gt;</text>
    <text x="15" y="82" font-size="10" fill="#64748b">• Transaction con PUT</text>
  </g>

  <!-- Transition TRANSFORMADO -> ENTREGADO -->
  <line x1="880" y1="200" x2="960" y2="200" stroke="#16a34a" stroke-width="2" marker-end="url(#earrow-ok)"/>
  <text x="920" y="190" text-anchor="middle" font-size="11" fill="#16a34a">HAPI &amp; DB OK</text>

  <!-- State 4: ENTREGADO -->
  <g transform="translate(960, 155)">
    <rect x="0" y="0" width="160" height="90" rx="12" fill="#f0fdf4" stroke="#16a34a" stroke-width="2.5" filter="url(#eshadow)"/>
    <rect x="0" y="0" width="160" height="28" rx="12" fill="#dcfce7"/>
    <text x="80" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#15803d">ENTREGADO</text>
    <text x="15" y="48" font-size="11" fill="#166534">• Guardado en HAPI</text>
    <text x="15" y="66" font-size="11" fill="#166534">• Guardado en Nodo</text>
    <text x="15" y="82" font-size="10" fill="#166534">• Hash encadenado</text>
  </g>
  <!-- Final state entregado -->
  <circle cx="1040" cy="300" r="16" fill="none" stroke="#16a34a" stroke-width="2"/>
  <circle cx="1040" cy="300" r="10" fill="#16a34a"/>
  <line x1="1040" y1="245" x2="1040" y2="284" stroke="#16a34a" stroke-width="2" marker-end="url(#earrow-ok)"/>

  <!-- State: REINTENTANDO -->
  <g transform="translate(690, 360)">
    <rect x="0" y="0" width="190" height="90" rx="12" fill="#ffffff" stroke="#eab308" stroke-width="2" filter="url(#eshadow)"/>
    <rect x="0" y="0" width="190" height="28" rx="12" fill="#fef9c3"/>
    <text x="95" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#a16207">REINTENTANDO</text>
    <text x="15" y="48" font-size="11" fill="#334155">• Espera exponencial</text>
    <text x="15" y="66" font-size="11" fill="#334155">• (1s, 2s, 4s, 8s...)</text>
    <text x="15" y="82" font-size="10" fill="#64748b">• intentos &lt;= 4</text>
  </g>
  <!-- Retry path -->
  <line x1="785" y1="245" x2="785" y2="360" stroke="#eab308" stroke-width="2" marker-end="url(#earrow)"/>
  <text x="795" y="300" font-size="11" fill="#a16207">Error HAPI / DB</text>

  <path d="M 880 405 Q 940 380 940 300 Q 940 220 885 220" stroke="#16a34a" stroke-width="1.5" stroke-dasharray="4,3" fill="none" marker-end="url(#earrow-ok)"/>
  <text x="945" y="320" font-size="11" fill="#15803d">Recupera</text>

  <!-- State: MUERTO (DLQ) -->
  <g transform="translate(690, 540)">
    <rect x="0" y="0" width="190" height="80" rx="12" fill="#450a0a" stroke="#dc2626" stroke-width="2" filter="url(#eshadow)"/>
    <rect x="0" y="0" width="190" height="28" rx="12" fill="#7f1d1d"/>
    <text x="95" y="20" text-anchor="middle" font-size="13" font-weight="bold" fill="#fca5a5">MUERTO (DLQ)</text>
    <text x="15" y="48" font-size="11" fill="#fee2e2">• Superó 4 intentos</text>
    <text x="15" y="66" font-size="11" fill="#fee2e2">• Requiere reencolado</text>
  </g>
  <!-- Final dead state -->
  <circle cx="940" cy="580" r="16" fill="none" stroke="#7f1d1d" stroke-width="2"/>
  <circle cx="940" cy="580" r="10" fill="#7f1d1d"/>
  <line x1="785" y1="450" x2="785" y2="540" stroke="#dc2626" stroke-width="2" marker-end="url(#earrow-err)"/>
  <text x="795" y="495" font-size="11" fill="#b91c1c">intentos &gt; 4</text>
  <line x1="880" y1="580" x2="924" y2="580" stroke="#7f1d1d" stroke-width="2" marker-end="url(#earrow-err)"/>
</svg>'''
    return svg

def create_svg_arquitectura():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 860" width="100%" height="100%" style="background:#f8fafc; font-family:system-ui, -apple-system, sans-serif;">
  <defs>
    <filter id="ashadow" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="2" dy="4" stdDeviation="5" flood-color="#0f172a" flood-opacity="0.08"/>
    </filter>
    <marker id="a-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563eb"/>
    </marker>
    <marker id="a-arrow-g" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#16a34a"/>
    </marker>
  </defs>

  <!-- Title -->
  <text x="600" y="40" text-anchor="middle" font-size="22" font-weight="bold" fill="#0f172a">Arquitectura Global de la Plataforma de Interoperabilidad en Salud</text>
  <text x="600" y="65" text-anchor="middle" font-size="14" fill="#64748b">Integración de Sedes Distribuidas, HSB, Servidor FHIR R4, Nodos PostgreSQL y Vistas por Rol</text>

  <!-- Layer 1: Sistemas Legados (Sedes) -->
  <rect x="50" y="90" width="1100" height="110" rx="14" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1.5" filter="url(#ashadow)"/>
  <text x="80" y="115" font-size="13" font-weight="bold" fill="#475569">1. CAPA DE SISTEMAS LEGADOS (3 SEDES DE SALUD)</text>
  
  <!-- Sede 1 Sincelejo -->
  <g transform="translate(80, 130)">
    <rect x="0" y="0" width="310" height="55" rx="8" fill="#ffffff" stroke="#4f46e5" stroke-width="1.5"/>
    <text x="20" y="24" font-size="13" font-weight="bold" fill="#312e81">Sede 1: Sincelejo (HIS Meditech)</text>
    <text x="20" y="44" font-size="11" fill="#6366f1">Emite: HL7 v2 ORU^R01 (Laboratorios)</text>
  </g>
  <!-- Sede 2 Cartagena -->
  <g transform="translate(440, 130)">
    <rect x="0" y="0" width="320" height="55" rx="8" fill="#ffffff" stroke="#4f46e5" stroke-width="1.5"/>
    <text x="20" y="24" font-size="13" font-weight="bold" fill="#312e81">Sede 2: Cartagena (HIS Servinte)</text>
    <text x="20" y="44" font-size="11" fill="#6366f1">Emite: HL7 v2 ADT^A01 (Admisión / Diagnóstico)</text>
  </g>
  <!-- Sede 3 Corozal -->
  <g transform="translate(810, 130)">
    <rect x="0" y="0" width="310" height="55" rx="8" fill="#ffffff" stroke="#4f46e5" stroke-width="1.5"/>
    <text x="20" y="24" font-size="13" font-weight="bold" fill="#312e81">Sede 3: Corozal (SISPRO Local)</text>
    <text x="20" y="44" font-size="11" fill="#6366f1">Emite: CSV Legado (Separador ;)</text>
  </g>

  <!-- Flow Arrows Down to HSB -->
  <line x1="235" y1="185" x2="235" y2="230" stroke="#2563eb" stroke-width="2" marker-end="url(#a-arrow)"/>
  <line x1="600" y1="185" x2="600" y2="230" stroke="#2563eb" stroke-width="2" marker-end="url(#a-arrow)"/>
  <line x1="965" y1="185" x2="965" y2="230" stroke="#2563eb" stroke-width="2" marker-end="url(#a-arrow)"/>

  <!-- Layer 2: HSB Service Bus -->
  <rect x="50" y="230" width="1100" height="150" rx="14" fill="#eff6ff" stroke="#3b82f6" stroke-width="2" filter="url(#ashadow)"/>
  <text x="80" y="255" font-size="14" font-weight="bold" fill="#1e40af">2. HEALTH SERVICE BUS (HSB) — FastAPI :8001 / Interno :8000</text>
  
  <g transform="translate(70, 270)">
    <rect x="0" y="0" width="200" height="90" rx="8" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5"/>
    <text x="15" y="22" font-size="12" font-weight="bold" fill="#1e3a8a">Ingesta &amp; Endpoints</text>
    <text x="15" y="42" font-size="11" fill="#334155">• POST /hsb/hl7</text>
    <text x="15" y="60" font-size="11" fill="#334155">• POST /hsb/csv?sede=N</text>
    <text x="15" y="78" font-size="11" fill="#334155">• GET /health &amp; /metrics</text>
  </g>

  <g transform="translate(290, 270)">
    <rect x="0" y="0" width="190" height="90" rx="8" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5"/>
    <text x="15" y="22" font-size="12" font-weight="bold" fill="#1e3a8a">Validación &amp; Idemp.</text>
    <text x="15" y="42" font-size="11" fill="#334155">• MSH-10 / Hash persistente</text>
    <text x="15" y="60" font-size="11" fill="#334155">• Doc numérico, Sexo M/F/O</text>
    <text x="15" y="78" font-size="11" fill="#334155">• Mapeo CIE-10 &amp; LOINC</text>
  </g>

  <g transform="translate(500, 270)">
    <rect x="0" y="0" width="200" height="90" rx="8" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5"/>
    <text x="15" y="22" font-size="12" font-weight="bold" fill="#1e3a8a">Normalizador FHIR R4</text>
    <text x="15" y="42" font-size="11" fill="#334155">• Patient (pac-&lt;doc&gt;)</text>
    <text x="15" y="60" font-size="11" fill="#334155">• Encounter, Condition</text>
    <text x="15" y="78" font-size="11" fill="#334155">• Observation en Bundle</text>
  </g>

  <g transform="translate(720, 270)">
    <rect x="0" y="0" width="200" height="90" rx="8" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5"/>
    <text x="15" y="22" font-size="12" font-weight="bold" fill="#1e3a8a">Cola Reintentos &amp; DLQ</text>
    <text x="15" y="42" font-size="11" fill="#334155">• Backoff (1s, 2s, 4s...)</text>
    <text x="15" y="60" font-size="11" fill="#334155">• Máximo 4 reintentos</text>
    <text x="15" y="78" font-size="11" fill="#334155">• Cola mensajes muertos</text>
  </g>

  <g transform="translate(940, 270)">
    <rect x="0" y="0" width="190" height="90" rx="8" fill="#ffffff" stroke="#93c5fd" stroke-width="1.5"/>
    <text x="15" y="22" font-size="12" font-weight="bold" fill="#1e3a8a">Auditoría Hash</text>
    <text x="15" y="42" font-size="11" fill="#334155">• SHA-256 encadenado</text>
    <text x="15" y="60" font-size="11" fill="#334155">• Inmutabilidad cripto</text>
    <text x="15" y="78" font-size="11" fill="#334155">• Verificador de integridad</text>
  </g>

  <!-- Flow to FHIR & DB -->
  <line x1="600" y1="380" x2="600" y2="420" stroke="#2563eb" stroke-width="2" marker-end="url(#a-arrow)"/>

  <!-- Layer 3: Servidores y Almacenamiento Distribuido -->
  <rect x="50" y="420" width="1100" height="150" rx="14" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#ashadow)"/>
  <text x="80" y="445" font-size="13" font-weight="bold" fill="#475569">3. CAPA DE SERVIDORES FHIR Y ALMACENAMIENTO DISTRIBUIDO</text>

  <!-- HAPI FHIR -->
  <g transform="translate(80, 460)">
    <rect x="0" y="0" width="230" height="90" rx="8" fill="#fff7ed" stroke="#ea580c" stroke-width="2"/>
    <text x="20" y="24" font-size="13" font-weight="bold" fill="#9a3412">HAPI FHIR Server R4</text>
    <text x="20" y="44" font-size="11" fill="#7c2d12">• Puerto :8090 / :8080</text>
    <text x="20" y="62" font-size="11" fill="#7c2d12">• Transaction PUT determinista</text>
    <text x="20" y="80" font-size="11" fill="#7c2d12">• /fhir/metadata, $validate</text>
  </g>

  <!-- Sede 1 DB -->
  <g transform="translate(340, 460)">
    <rect x="0" y="0" width="180" height="90" rx="8" fill="#ffffff" stroke="#6d28d9" stroke-width="1.5"/>
    <text x="15" y="22" font-size="12" font-weight="bold" fill="#4c1d95">pg_sede1 (:5431)</text>
    <text x="15" y="42" font-size="11" fill="#334155">Sincelejo</text>
    <text x="15" y="60" font-size="10" fill="#64748b">historia_clinica_sede1</text>
    <text x="15" y="78" font-size="10" fill="#64748b">Healthcheck: pg_isready</text>
  </g>

  <!-- Sede 2 DB -->
  <g transform="translate(540, 460)">
    <rect x="0" y="0" width="180" height="90" rx="8" fill="#ffffff" stroke="#6d28d9" stroke-width="1.5"/>
    <text x="15" y="22" font-size="12" font-weight="bold" fill="#4c1d95">pg_sede2 (:5432)</text>
    <text x="15" y="42" font-size="11" fill="#334155">Cartagena</text>
    <text x="15" y="60" font-size="10" fill="#64748b">historia_clinica_sede2</text>
    <text x="15" y="78" font-size="10" fill="#64748b">Healthcheck: pg_isready</text>
  </g>

  <!-- Sede 3 DB -->
  <g transform="translate(740, 460)">
    <rect x="0" y="0" width="180" height="90" rx="8" fill="#ffffff" stroke="#6d28d9" stroke-width="1.5"/>
    <text x="15" y="22" font-size="12" font-weight="bold" fill="#4c1d95">pg_sede3 (:5433)</text>
    <text x="15" y="42" font-size="11" fill="#334155">Corozal</text>
    <text x="15" y="60" font-size="10" fill="#64748b">historia_clinica_sede3</text>
    <text x="15" y="78" font-size="10" fill="#64748b">Healthcheck: pg_isready</text>
  </g>

  <!-- Audit DB -->
  <g transform="translate(940, 460)">
    <rect x="0" y="0" width="180" height="90" rx="8" fill="#ecfdf5" stroke="#059669" stroke-width="1.5"/>
    <text x="15" y="22" font-size="12" font-weight="bold" fill="#047857">hsb_audit_db</text>
    <text x="15" y="42" font-size="11" fill="#334155">Trazabilidad</text>
    <text x="15" y="60" font-size="10" fill="#64748b">evento_auditoria</text>
    <text x="15" y="78" font-size="10" fill="#64748b">Cadena SHA-256</text>
  </g>

  <!-- Layer 4: Aplicación Web y 4 Vistas -->
  <rect x="50" y="610" width="1100" height="200" rx="14" fill="#ffffff" stroke="#2563eb" stroke-width="2" filter="url(#ashadow)"/>
  <text x="80" y="635" font-size="14" font-weight="bold" fill="#1e3a8a">4. CAPA DE APLICACIÓN Y LAS 4 VISTAS POR ROL (FastAPI Gateway + Web UI :5000)</text>
  <text x="80" y="655" font-size="12" fill="#64748b">Seguridad RBAC con JWT • Consulta Unificada Multi-Sede Tolerante a Fallos Parciales (Degradación)</text>

  <!-- Vista Paciente -->
  <g transform="translate(70, 675)">
    <rect x="0" y="0" width="250" height="115" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
    <text x="15" y="22" font-size="13" font-weight="bold" fill="#15803d">Vista Paciente</text>
    <text x="15" y="42" font-size="11" fill="#334155">• Login con su documento</text>
    <text x="15" y="60" font-size="11" fill="#334155">• HC unificada ordenada cronológico</text>
    <text x="15" y="78" font-size="11" fill="#334155">• Botón descargar Bundle FHIR</text>
    <text x="15" y="96" font-size="11" fill="#334155">• Ver quién accedió a su historia</text>
  </g>

  <!-- Vista Admisionista -->
  <g transform="translate(340, 675)">
    <rect x="0" y="0" width="250" height="115" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
    <text x="15" y="22" font-size="13" font-weight="bold" fill="#1d4ed8">Vista Admisionista</text>
    <text x="15" y="42" font-size="11" fill="#334155">• Búsqueda por documento</text>
    <text x="15" y="60" font-size="11" fill="#334155">• Detección sedes donde existe</text>
    <text x="15" y="78" font-size="11" fill="#334155">• Formulario admisión con triage</text>
    <text x="15" y="96" font-size="11" fill="#334155">• Monitoreo mensajes HSB (sin dx)</text>
  </g>

  <!-- Vista Médico -->
  <g transform="translate(610, 675)">
    <rect x="0" y="0" width="250" height="115" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
    <text x="15" y="22" font-size="13" font-weight="bold" fill="#b45309">Vista Médico</text>
    <text x="15" y="42" font-size="11" fill="#334155">• HC completa de las 3 sedes</text>
    <text x="15" y="60" font-size="11" fill="#334155">• Registrar diagnóstico CIE-10</text>
    <text x="15" y="78" font-size="11" fill="#334155">• Ordenar tecnologías / medicación</text>
    <text x="15" y="96" font-size="11" fill="#334155">• Egreso clínico con sello SHA-256</text>
  </g>

  <!-- Vista Reporte de HC -->
  <g transform="translate(880, 675)">
    <rect x="0" y="0" width="250" height="115" rx="8" fill="#faf5ff" stroke="#7e22ce" stroke-width="1.5"/>
    <text x="15" y="22" font-size="13" font-weight="bold" fill="#6b21a8">Reporte HC &amp; Monitoreo</text>
    <text x="15" y="42" font-size="11" fill="#334155">• Reporte agrupado por sede</text>
    <text x="15" y="60" font-size="11" fill="#334155">• Cobertura % campos y faltantes</text>
    <text x="15" y="78" font-size="11" fill="#334155">• Sello integridad / Imprimir / FHIR</text>
    <text x="15" y="96" font-size="11" fill="#334155">• Tablero: nodos, métricas, hash</text>
  </g>

  <!-- Two way arrows between Layer 3 & 4 -->
  <line x1="600" y1="570" x2="600" y2="610" stroke="#16a34a" stroke-width="2" marker-end="url(#a-arrow-g)"/>
</svg>'''
    return svg

def main():
    diagrams = {
        'casos_de_uso.svg': create_svg_casos_de_uso(),
        'secuencia.svg': create_svg_secuencia(),
        'clases.svg': create_svg_clases(),
        'estados.svg': create_svg_estados(),
        'arquitectura.svg': create_svg_arquitectura()
    }
    for filename, content in diagrams.items():
        path = os.path.join(SVG_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Generated: {path}")

if __name__ == '__main__':
    main()
