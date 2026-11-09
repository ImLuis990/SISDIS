# Plataforma Distribuida de Interoperabilidad Clínica
### Parcial Final — Sistemas Distribuidos

**Institución:** Corporación Universitaria Antonio José de Sucre  
**Docente:** Ing. Jaider Enrique Reyes Herazo  
**Periodo:** 2026-I

| Integrante | Correo | Rol principal |
|---|---|---|
| Luis Fernando Rios Barboza | luis.rios@corposucre.edu.co | Arquitectura HSB, Parser HL7/CSV, Seguridad, Web App |
| Jaime Andrés Villarreal Parra | jaime.villarreal@corposucre.edu.co | Modelo de datos, FHIR R4, ACID, Despliegue |

---

## Descripción

Sistema de salud distribuido que interconecta tres sedes hospitalarias (Sincelejo, Cartagena, Corozal) mediante un **Health Service Bus (HSB)** con soporte para:

- Mensajes **HL7 v2.x** (ADT^A01, ORU^R01)
- Archivos **CSV** de sistemas legados
- Normalización a **FHIR R4** y publicación en servidor HAPI-FHIR
- **Control de acceso basado en roles** (RBAC) con JWT + HMAC-SHA256
- **Auditoría de integridad** con cadena de hashes SHA-256
- **Resiliencia** con degraded-mode y reintento exponencial
- **4 vistas web** (Paciente, Admisionista, Médico, Auditor)

---

## Requisitos

- Docker ≥ 24.x
- docker compose (plugin v2)

```bash
docker --version
docker compose version
```

---

## Inicio rápido

### 1. Clonar y levantar el stack completo

```bash
git clone <repo-url> && cd SISDIS   # o simplemente entrar al directorio
docker compose down -v               # limpia estado previo
docker compose up --build -d         # construye e inicia todos los servicios
```

Esperar ~60 segundos a que los contenedores estén healthy:

```bash
docker compose ps
```

### 2. Verificar que los servicios están activos

| Servicio | URL | Descripción |
|---|---|---|
| Web App | http://localhost:5000 | Interfaz gráfica con 4 vistas |
| HSB Service | http://localhost:8001/health | Health Service Bus API |
| HAPI FHIR | http://localhost:8090/fhir/metadata | Servidor FHIR R4 |
| PostgreSQL Sede 1 | localhost:5431 | Sincelejo |
| PostgreSQL Sede 2 | localhost:5432 | Cartagena |
| PostgreSQL Sede 3 | localhost:5433 | Corozal |

---

## Usuarios de prueba

| Usuario | Contraseña | Rol | Acceso |
|---|---|---|---|
| `1001` | `pass1001` | paciente | Solo su propia historia clínica |
| `1007` | `pass1007` | paciente | Solo su propia historia clínica |
| `admision1` | `admision123` | admisionista | Búsqueda y admisión de pacientes |
| `medico1` | `medico123` | medico | Historia completa + registro de atenciones |
| `auditor1` | `auditor123` | auditor | Métricas globales + verificación de integridad |

---

## Envío de mensajes de ejemplo

Los archivos de ejemplo se encuentran en `ejemplos/`. El guión de demostración automatiza todos los pasos:

```bash
bash demo_guion.sh
```

O manualmente:

### HL7 ADT^A01 válido (Sede 2)
```bash
curl -s -X POST \
  -H "Content-Type: text/plain" \
  --data-binary @ejemplos/01_adt_a01_valido_sede2.hl7 \
  http://localhost:8001/hsb/hl7
```
**Resultado esperado:** `"estado":"ENTREGADO"`, Patient CC 1007, J45.9, Sede 2

### HL7 ORU^R01 laboratorio (Sede 1)
```bash
curl -s -X POST \
  -H "Content-Type: text/plain" \
  --data-binary @ejemplos/02_oru_r01_laboratorio_sede1.hl7 \
  http://localhost:8001/hsb/hl7
```
**Resultado esperado:** `"estado":"ENTREGADO"`, Obs 718-7 = 13.8 g/dL, Sede 1

### HL7 ADT^A01 inválido (3 motivos de rechazo)
```bash
curl -s -X POST \
  -H "Content-Type: text/plain" \
  --data-binary @ejemplos/03_adt_a01_invalido.hl7 \
  http://localhost:8001/hsb/hl7
```
**Resultado esperado:** `"estado":"RECHAZADO"`, 3 motivos

### CSV legado Sede 3 (batch)
```bash
curl -s -X POST \
  -H "Content-Type: text/plain" \
  --data-binary @ejemplos/04_sede3_legado.csv \
  http://localhost:8001/hsb/csv
```
**Resultado esperado:** 3 ENTREGADOS, 2 RECHAZADOS

---

## Simulación de caída de sede (resiliencia)

```bash
# Apagar Sede 2
docker stop pg_sede2

# Consultar paciente 1001 (el sistema responde en modo degradado)
curl -s http://localhost:5000/api/paciente/1001/historia

# Restaurar
docker start pg_sede2
```

---

## Endpoints del HSB

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/hsb/hl7` | Ingerir mensaje HL7 v2 |
| POST | `/hsb/csv` | Ingerir archivo CSV legado |
| GET | `/hsb/mensajes` | Listar todos los mensajes procesados |
| GET | `/health` | Health check |
| GET | `/metrics` | Métricas operacionales |
| GET | `/hsb/auditoria` | Cadena de auditoría |
| POST | `/hsb/auditoria/verificar` | Verificar integridad de la cadena |
| POST | `/hsb/reintentar-dlq` | Reintentar mensajes en Dead Letter Queue |

---

## Endpoints de la Web App

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/api/auth/login` | Autenticación, retorna JWT |
| GET | `/api/paciente/{doc}/historia` | Historia clínica unificada (requiere JWT) |
| GET | `/api/paciente/{doc}/bundle-fhir` | Bundle FHIR R4 del paciente |
| GET | `/api/admision/buscar/{doc}` | Buscar paciente (rol admisionista) |
| POST | `/api/admision/admitir` | Registrar admisión con triage |
| POST | `/api/medico/atencion` | Registrar atención médica |
| GET | `/metrics` | Métricas globales (rol auditor) |
| POST | `/hsb/auditoria/verificar` | Verificar cadena (rol auditor) |

---

## Ejecutar pruebas unitarias e integración

> Las pruebas usan solo biblioteca estándar de Python 3; no se requiere Docker.

```bash
python3 -m unittest discover -s tests -v
```

**26 pruebas, 100% aprobadas** (en < 0.01 s)

---

## Estructura del proyecto

```
SISDIS/
├── app/                        # Web App FastAPI (puerto 5000)
│   ├── main.py                 # API Gateway + vistas
│   ├── seguridad.py            # JWT + RBAC
│   ├── consulta_unificada.py   # Motor de consulta distribuida
│   ├── verificador_auditoria.py
│   ├── templates/index.html    # 4 vistas Bootstrap 5
│   └── Dockerfile
├── hsb/                        # Health Service Bus (puerto 8001)
│   ├── service.py              # Orquestador principal
│   ├── parser_hl7.py           # Parser HL7 v2
│   ├── parser_csv.py           # Parser CSV legado
│   ├── terminologia.py         # Mapeo CIE-10 ↔ SNOMED ↔ LOINC
│   ├── main.py                 # FastAPI
│   └── Dockerfile
├── fhir/
│   └── normalizador.py         # Normalización a FHIR R4
├── db/
│   ├── init/                   # Scripts SQL (schema + 3 sedes + terminología)
│   └── demo_acid.py            # Demo transacciones ACID
├── docs/
│   ├── uml/                    # 5 diagramas PlantUML + SVG
│   ├── 01_FASE1_ANALISIS_UML_DISENO.md
│   ├── 02_FASE2_DATOS_DISTRIBUIDOS_FHIR.md
│   ├── 03_FASE3_HSB_MIDDLEWARE.md
│   ├── 04_FASE4_SEGURIDAD_RESILIENCIA_DESPLIEGUE.md
│   └── 05_FASE5_PROTOTIPO_INFORME_SUSTENTACION.md
├── infra/k8s/                  # Manifiestos Kubernetes (bonus)
├── tests/                      # 26 pruebas unitarias/integración
├── ejemplos/                   # Archivos de contrato (no modificar)
├── docker-compose.yml          # Stack completo (6 servicios)
├── demo_guion.sh               # Guión de demostración 7 pasos
└── README.md
```

---

## Decisiones de diseño clave

| Decisión | Alternativa considerada | Por qué se eligió |
|---|---|---|
| HMAC-SHA256 JWT propio | PyJWT / python-jose | Sin dependencias externas; control total sobre claims |
| Idempotencia en memoria | Redis / PostgreSQL | Simplicidad; para producción se externalizaría a BD |
| Reintento exponencial (1s, 2s, 4s, 8s) | Circuit breaker completo | Equilibrio entre resiliencia y complejidad |
| FHIR IDs deterministas (`pac-<doc>`) | UUIDs aleatorios | Idempotencia en PUT; misma cédula → mismo recurso |
| `python:3.11-slim` base image | Alpine | Compatibilidad con cryptography sin wheels especiales |

---

## Versión

`v1.0` — Plataforma de Interoperabilidad Clínica — Parcial Final 2026-I
