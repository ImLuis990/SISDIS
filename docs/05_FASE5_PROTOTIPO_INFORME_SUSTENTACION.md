# Fase 5 — Prototipo Final, Integración y Sustentación

**Proyecto:** Plataforma Distribuida de Interoperabilidad Clínica  
**Institución:** Corporación Universitaria Antonio José de Sucre  
**Docente:** Ing. Jaider Enrique Reyes Herazo  
**Equipo:**
- Luis Fernando Rios Barboza — luis.rios@corposucre.edu.co
- Jaime Andrés Villarreal Parra — jaime.villarreal@corposucre.edu.co

---

## 1. Resumen Ejecutivo

La Fase 5 integra todos los componentes construidos en las fases anteriores en un **prototipo funcional completo** desplegable con un único comando `docker compose up`. La plataforma demuestra interoperabilidad clínica real entre tres sedes hospitalarias distribuidas, con soporte para los estándares HL7 v2 y FHIR R4, seguridad basada en roles, auditoría de integridad y resiliencia ante fallos de nodos.

**Resultados del guión de demostración (7 pasos, todos exitosos):**

| Paso | Descripción | Resultado |
|---|---|---|
| 1 | Suite de pruebas unitarias e integración | 26/26 ✅ |
| 2 | HL7 ADT^A01 válido (Sede 2, CC 1007, J45.9) | ENTREGADO ✅ |
| 3 | HL7 ORU^R01 laboratorio (Sede 1, 718-7, 13.8 g/dL) | ENTREGADO ✅ |
| 4 | HL7 ADT^A01 inválido (3 motivos exactos de rechazo) | RECHAZADO ✅ |
| 5 | CSV legado Sede 3 (batch de 5 filas) | 3 ENTREGADOS, 2 RECHAZADOS ✅ |
| 6 | Idempotencia (reenvío file 01) | DUPLICADO detectado ✅ |
| 7 | Resiliencia y auditoría de integridad | Degraded mode + tampering detectado ✅ |

---

## 2. Arquitectura Final Implementada

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTES WEB                             │
│         Paciente │ Admisionista │ Médico │ Auditor              │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP + JWT (puerto 5000)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WEB APP (FastAPI)                             │
│  • Autenticación JWT + HMAC-SHA256                              │
│  • RBAC: 4 roles, habeas data enforced                          │
│  • API Gateway → HSB Service                                    │
│  • 4 vistas Bootstrap 5                                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP REST (puerto 8001)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               HEALTH SERVICE BUS (HSB)                          │
│  • Parser HL7 v2 (ADT^A01, ORU^R01)                            │
│  • Parser CSV legado                                            │
│  • Validación multicapa (estructura, semántica, terminología)   │
│  • Idempotencia SHA-256                                         │
│  • Transformación → FHIR R4 (NormalizadorFHIR)                 │
│  • Reintento exponencial (1s, 2s, 4s, 8s, max 4 reintentos)    │
│  • Dead Letter Queue (DLQ)                                      │
│  • Cadena de auditoría SHA-256                                  │
└──────────┬──────────────────────────────┬───────────────────────┘
           │ PUT /fhir                    │ SQL
           ▼                             ▼
┌─────────────────────┐    ┌─────────────────────────────────────┐
│   HAPI FHIR R4      │    │  PostgreSQL (3 instancias)          │
│   puerto 8090       │    │  Sede 1 :5431 — Sincelejo           │
│   Bundle PUT TX     │    │  Sede 2 :5432 — Cartagena           │
│   deterministic IDs │    │  Sede 3 :5433 — Corozal             │
└─────────────────────┘    └─────────────────────────────────────┘
```

### Componentes por servicio Docker

| Contenedor | Imagen | Puerto | Rol |
|---|---|---|---|
| `web-app` | python:3.11-slim | 5000 | Interfaz gráfica + API Gateway |
| `hsb-service` | python:3.11-slim | 8001 | Health Service Bus |
| `hapi-fhir` | hapiproject/hapi:latest | 8090 | Servidor FHIR R4 |
| `pg_sede1` | postgres:15 | 5431 | BD Sincelejo |
| `pg_sede2` | postgres:15 | 5432 | BD Cartagena |
| `pg_sede3` | postgres:15 | 5433 | BD Corozal |

---

## 3. Vistas Web Implementadas

### Vista 1 — Paciente (acceso propio)
- Login con cédula + contraseña → JWT emitido
- Consulta historia clínica unificada (sedes 1, 2 y 3)
- Visualización de diagnósticos CIE-10, procedimientos LOINC
- Descarga Bundle FHIR R4 (JSON)
- Impresión / PDF del resumen
- **Habeas Data:** solo puede ver sus propios registros; cualquier intento de ver registros ajenos retorna 403

### Vista 2 — Admisionista (ingreso de pacientes)
- Búsqueda de paciente por cédula
- Formulario de admisión con triage (I/II/III/IV/V)
- Genera y envía mensaje HL7 ADT^A01 al HSB
- Visualiza estado del bus (mensajes procesados, rechazados, DLQ)

### Vista 3 — Médico (atención clínica)
- Consulta historia completa del paciente
- Formulario de atención: diagnóstico CIE-10, LOINC, notas
- Registro sellado criptográficamente (hash SHA-256 del contenido + timestamp)
- Validación de terminología en tiempo real (CIE-10 + LOINC)

### Vista 4 — Auditor (control y métricas)
- Dashboard de métricas: mensajes procesados/rechazados/DLQ por período
- Verificación de integridad de la cadena de auditoría
- Simulación de alteración para demostrar detección
- Exportación de log de auditoría

### Tablero de Estado (accesible a todos los roles)
- Estado de cada sede (UP/DOWN/DEGRADED)
- Cobertura FHIR de la red
- Conteo de pacientes por sede
- Tiempo de última sincronización

---

## 4. Resultados Medidos

### 4.1 Procesamiento de mensajes de contrato

#### Archivo 01 — `01_adt_a01_valido_sede2.hl7`
```
Estado:        ENTREGADO
Paciente:      CC 1007 (J. Martínez)
Diagnóstico:   J45.9 (Asma sin especificar) → SNOMED 195967001
Sede:          2 (Cartagena)
FHIR IDs:      Patient/pac-1007, Encounter/enc-201, Condition/cond-201-J45.9
```

#### Archivo 02 — `02_oru_r01_laboratorio_sede1.hl7`
```
Estado:        ENTREGADO
Paciente:      CC 1004 (Ana Díaz)
Observación:   LOINC 718-7 (Hemoglobina) = 13.8 g/dL
Sede:          1 (Sincelejo)
FHIR IDs:      Patient/pac-1004, Encounter/enc-401, Observation/obs-401-718-7
```

#### Archivo 03 — `03_adt_a01_invalido.hl7`
```
Estado:        RECHAZADO
Motivos (3):
  1. Fecha de nacimiento inválida o ausente
  2. Diagnóstico CIE-10 sin mapeo de terminología
  3. Identificación del paciente inválida o ausente
```

#### Archivo 04 — `04_sede3_legado.csv`
```
Total filas:   5
ENTREGADOS:    3 (CC 2001, 2003, 2005)
RECHAZADOS:    2 (CC 2002 — sin CIE-10 válido; CC 2004 — sin DOC)
```

### 4.2 Idempotencia

Reenvío del mismo mensaje (file 01) produce estado `DUPLICADO`; no se crea un segundo recurso en HAPI FHIR. La clave de idempotencia es el hash SHA-256 del contenido completo del mensaje.

### 4.3 Resiliencia

| Escenario | Comportamiento | Tiempo de respuesta |
|---|---|---|
| Todas las sedes UP | Historia completa con datos de 3 sedes | < 50 ms |
| Sede 2 DOWN | Degraded mode: datos de sedes 1 y 3 + advertencia | < 50 ms |
| HAPI FHIR DOWN | Reintento 4 veces (backoff exponencial) → DLQ | ~15 s total |
| Reintentar DLQ | Mensajes en cola se re-procesan exitosamente | < 1 s |

### 4.4 Integridad de auditoría

- Cadena de hashes verificada: `OK` para eventos no alterados
- Al alterar el contenido de un evento, el verificador detecta ruptura en la cadena:
  ```
  ALERTA: Integridad comprometida en evento #2
  Hash calculado: a3f2c1... ≠ Hash registrado: b8e9d4...
  ```

### 4.5 Suite de pruebas

| Módulo | Pruebas | Estado |
|---|---|---|
| `test_normalizador_fhir.py` | 7 | ✅ |
| `test_acid.py` | 2 | ✅ |
| `test_hsb_mensajes.py` | 6 | ✅ |
| `test_seguridad_roles.py` | 5 | ✅ |
| `test_auditoria_integridad.py` | 3 | ✅ |
| `test_resiliencia.py` | 3 | ✅ |
| **TOTAL** | **26** | **100% ✅** |

---

## 5. Estándares y Especificaciones Implementadas

### HL7 v2.x
- **ADT^A01** (Admit / Visit Notification): Segmentos MSH, EVN, PID, PV1, DG1
- **ORU^R01** (Observation Result): Segmentos MSH, PID, PV1, OBR, OBX
- Separador de segmentos: `\r` (carriage return, standard HL7)
- Codificación de campos: `|^~\&` (delimitadores estándar)

### FHIR R4
- **Patient** con identificador NationalPassport (cédula colombiana)
- **Encounter** con período de admisión/egreso
- **Condition** con código CIE-10 mapeado
- **Observation** con código LOINC, valor y unidad UCUM
- **Bundle** de tipo `transaction` con método PUT e IDs deterministas
- Endpoints FHIR: `PUT /fhir/Patient/pac-{doc}`, `PUT /fhir/Encounter/enc-{id}`, etc.

### Terminología médica
| Sistema origen | Sistema destino | Ejemplos |
|---|---|---|
| Código local | CIE-10 | fiebre→R50.9, diabetes→E11.9 |
| CIE-10 | SNOMED CT | J45.9→195967001, E11→73211009 |
| Código local | LOINC | hemoglobina→718-7, glucosa→2345-7 |
| LOINC | Nombre estándar | 718-7→Hemoglobin [Mass/volume], 2160-0→Creatinine |

---

## 6. Seguridad Implementada

### JWT propio (sin dependencias externas)
```
Header:  {"alg": "HS256", "typ": "JWT"}
Payload: {"sub": "medico1", "rol": "medico", "iat": ..., "exp": ...}
Firma:   HMAC-SHA256(base64url(header) + "." + base64url(payload), SECRET_KEY)
```

### Control de Acceso Basado en Roles (RBAC)

| Recurso | paciente | admisionista | medico | auditor |
|---|---|---|---|---|
| `/api/paciente/{doc}/historia` | Solo propio | ✗ | ✓ cualquier | ✓ cualquier |
| `/api/paciente/{doc}/bundle-fhir` | Solo propio | ✗ | ✓ | ✓ |
| `/api/admision/*` | ✗ | ✓ | ✗ | ✗ |
| `/api/medico/atencion` | ✗ | ✗ | ✓ | ✗ |
| `/metrics` | ✗ | ✗ | ✗ | ✓ |
| `/hsb/auditoria/verificar` | ✗ | ✗ | ✗ | ✓ |

### Habeas Data (Ley 1581/2012 — Colombia)
Un paciente que intenta consultar la historia de otro paciente recibe `403 Forbidden` con mensaje: *"Acceso denegado: solo puede consultar su propia historia clínica"*.

---

## 7. Decisiones de Diseño

### 7.1 Por qué un HSB centralizado vs. comunicación directa entre sedes
El HSB actúa como mediador que abstrae las diferencias de protocolo (HL7 v2 vs CSV vs FHIR). Permite validación centralizada, auditoría completa y un único punto de reintentos y DLQ, en lugar de lógica duplicada en cada sede.

### 7.2 Por qué IDs FHIR deterministas
Al usar `pac-{cedula}`, `enc-{id}`, el mismo mensaje enviado dos veces produce exactamente el mismo `PUT` en FHIR, haciendo la operación **idempotente por diseño**. Con UUIDs aleatorios, el mismo paciente generaría múltiples recursos duplicados en el servidor FHIR.

### 7.3 Por qué HMAC-SHA256 propio y no PyJWT
La guía requiere que el sistema funcione sin dependencias externas complejas y con control total del proceso de firma. HMAC-SHA256 está en la biblioteca estándar de Python (`hmac`, `hashlib`). La implementación es transparente y auditable.

### 7.4 Por qué backoff exponencial y no circuit breaker completo
Para el alcance del parcial, el backoff exponencial (1s→2s→4s→8s) es suficiente para demostrar resiliencia. Un circuit breaker completo requeriría monitoreo de estado del circuito (CERRADO/ABIERTO/SEMIABIERTO) que añadiría complejidad sin agregar valor pedagógico adicional.

### 7.5 Por qué tres instancias PostgreSQL separadas
Simula la realidad de hospitales en ciudades distintas (Sincelejo, Cartagena, Corozal) con bases de datos independientes que no comparten estado. El paciente CC 1001 (Carlos Pérez) tiene registros en las tres sedes, demostrando la necesidad de la consulta unificada.

---

## 8. Lecciones Aprendidas

1. **La idempotencia debe ser una decisión de diseño temprana.** Implementarla retroactivamente es costoso. El uso de hashes SHA-256 como clave de idempotencia resultó natural y eficiente.

2. **Los estándares HL7 v2 tienen muchas variaciones en la práctica.** Los mensajes reales usan `\r` como separador de segmentos y los sistemas legados a veces los envían como una sola línea. El parser debe ser robusto a estas variaciones.

3. **FHIR R4 impone una curva de aprendizaje significativa.** La estructura de Bundle de tipo `transaction` con `PUT` y `fullUrl` require entender el modelo de recursos FHIR antes de poder implementarlo.

4. **La cadena de auditoría con hashes encadenados es un patrón poderoso.** Similar a blockchain, garantiza que incluso un pequeño cambio en un evento rompe toda la cadena subsiguiente, haciendo el fraude detectable de inmediato.

5. **Docker Compose simplifica enormemente el despliegue distribuido.** Levantar 6 servicios coordinados (3 BD + FHIR + HSB + Web) con un solo comando es el resultado de una buena definición de `healthcheck` y `depends_on`.

---

## 9. Instrucciones de Sustentación

### Escenario recomendado (20 minutos)

**Minutos 0-3:** Presentación de la arquitectura (diagrama `docs/uml/arquitectura.svg`)

**Minutos 3-8:** Ejecución del guión de demostración
```bash
bash demo_guion.sh
```
Mostrar en vivo los 7 pasos y sus resultados.

**Minutos 8-13:** Demostración de la interfaz web (http://localhost:5000)
- Login como `paciente` (CC 1001) → historia clínica de las 3 sedes
- Login como `admisionista` → admitir paciente → ver mensaje en HSB
- Login como `medico` → registrar atención → sello criptográfico
- Login como `auditor` → verificar integridad → simular alteración → detectar

**Minutos 13-16:** Demostración de resiliencia
```bash
docker stop pg_sede2  # sede cae
# refrescar la vista paciente → modo degradado
docker start pg_sede2  # sede recupera
# refrescar → historia completa de nuevo
```

**Minutos 16-20:** Preguntas del docente

### Preguntas frecuentes esperadas

**P: ¿Cómo garantizan que el mismo mensaje no se procese dos veces?**  
R: Calculamos SHA-256 del contenido completo del mensaje. Antes de procesarlo, buscamos esa clave en el diccionario de idempotencia. Si ya existe, retornamos estado `DUPLICADO` sin re-procesar ni crear recursos FHIR duplicados.

**P: ¿Qué pasa si el servidor FHIR está caído?**  
R: El HSB reintenta 4 veces con backoff exponencial (1, 2, 4, 8 segundos). Si todos los reintentos fallan, el mensaje va a la Dead Letter Queue (DLQ) y puede reintentarse manualmente con `POST /hsb/reintentar-dlq`.

**P: ¿Cómo implementaron RBAC sin una librería de autorización?**  
R: Cada endpoint verifica el claim `rol` del JWT. La función `verificar_acceso()` en `seguridad.py` recibe el token y el recurso solicitado, y aplica las reglas de acceso definidas en la matriz de permisos, incluyendo la regla de Habeas Data para el rol `paciente`.

**P: ¿Por qué usaron IDs deterministas en FHIR?**  
R: Para que el `PUT /fhir/Patient/pac-1001` siempre actualice el mismo recurso, independientemente de cuántas veces se envíe el mensaje. Con UUIDs aleatorios, el mismo paciente generaría múltiples Patient FHIR duplicados, violando la unicidad del registro médico.

---

## 10. Repositorio Git

### Historial de commits

| Hash | Fase | Autor | Descripción |
|---|---|---|---|
| `b183b92` | 1 | Luis Rios | feat(fase1): analisis, modelado UML (4 diagramas SVG) y diseno de arquitectura |
| `60d15a1` | 2 | Jaime Villarreal | feat(fase2): esquema BD distribuida (3 sedes), semilla de datos, normalizador FHIR R4 |
| `e85755b` | 3 | Luis Rios | feat(fase3): HSB completo — parsers HL7/CSV, terminologia, servicio orquestador |
| `7fd6ca8` | 4 | Jaime Villarreal | feat(fase4): seguridad JWT+RBAC, auditoria integridad, resiliencia, k8s |
| `(fase5)` | 5 | Luis Rios | feat(fase5): prototipo final, 4 vistas web, docker-compose, README, sustentacion |

### Tag de entrega
```
v1.0 — Plataforma de Interoperabilidad Clínica — Parcial Final 2026-I
```
