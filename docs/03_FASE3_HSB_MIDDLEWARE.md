# Fase 3: Bus de Servicios de Salud (HSB) y Middleware de Integración

**Proyecto:** Plataforma Distribuida de Interoperabilidad Clínica Multi-Sede  
**Asignatura:** Sistemas Distribuidos  
**Institución:** Corporación Universitaria Antonio José de Sucre  
**Equipo de Desarrollo:**
- Luis Fernando Rios Barboza (luis.rios@corposucre.edu.co)
- Jaime Andrés Villarreal Parra (jaime.villarreal@corposucre.edu.co)  
**Docente:** Ing. Jaider Enrique Reyes Herazo  
**Fecha:** Noviembre de 2026

---

## 1. Justificación de la Herramienta HSB

Para la implementación del Bus de Servicios de Salud (HSB) se compararon cuatro alternativas tecnológicas:

| Criterio | HSB Propio (FastAPI + Python) | Mirth Connect (NextGen) | Apache Camel | OpenHIM |
|---|---|---|---|---|
| **Compatibilidad HL7 v2 y FHIR** | Nativa y personalizable (R4, ADT, ORU) | Excelente para v2; FHIR requiere plugins | Buena mediante conectores | Enfoque principal en FHIR |
| **Consumo de Memoria RAM** | **Muy bajo (< 80 MB)** | Alto (> 1.2 GB en JVM) | Medio (> 500 MB en JVM) | Medio (> 400 MB en Node.js) |
| **Manejo de Idempotencia Persistente** | Totalmente integrado con clave MSH-10 y Hash | Requiere script en base de datos externa | Requiere IdempotentConsumer EIP | Requiere base de datos MongoDB |
| **Auditoría Encadenada SHA-256** | Nativa en el pipeline de mensajería | No nativa (requiere custom transformer) | No nativa | Logs estándar sin hash |
| **Curva de Aprendizaje y Mantenimiento** | Baja y código abierto estándar | Alta (configuración por GUI Java) | Media-Alta (DSL Java/XML) | Media |
| **Licencia** | MIT / Código Abierto | Mozilla Public License | Apache 2.0 | GPL v3 |

**Decisión Técnica:** Se seleccionó el desarrollo del HSB como servicio propio en FastAPI debido a su eficiencia de memoria, soporte nativo de asincronía, tipado estático con Pydantic, cálculo directo de hashes criptográficos para auditoría y facilidad de despliegue en un contenedor ligero de menos de 180 MB.

---

## 2. Interoperabilidad Técnica y Semántica

### 2.1 Interoperabilidad Técnica
Se implementaron dos puertas de entrada RESTful:
- `POST /hsb/hl7`: Ingesta de mensajes HL7 v2 (delimitados por tuberías `|` y sombreritos `^`), soportando eventos `ADT^A01` (admisión/diagnóstico) y `ORU^R01` (resultados de observación diagnóstica).
- `POST /hsb/csv?sede=N`: Ingesta de archivos legados tabulares con delimitador de punto y coma (`;`), enrutando por parámetro o cabecera a la sede correspondiente (1, 2 o 3).

### 2.2 Interoperabilidad Semántica
El HSB resuelve la disparidad de vocabularios clínicos mediante la tabla de referencia `ref_terminologia`:
- **Diagnósticos Locales a CIE-10:**
  - `DIARREA` $\rightarrow$ `A09` (Diarrea y gastroenteritis)
  - `HIPERTENSION` $\rightarrow$ `I10` (Hipertensión esencial)
  - `DIABETES` $\rightarrow$ `E11.9` (Diabetes mellitus tipo 2)
  - `ASMA` $\rightarrow$ `J45.9` (Asma)
  - `INFECCION URINARIA` $\rightarrow$ `N39.0` (Infección de vías urinarias)
  - `LUMBAGO` $\rightarrow$ `M54.5` (Lumbago)
  - `NEUMONIA` $\rightarrow$ `J18.9` (Neumonía)
  - `CEFALEA` $\rightarrow$ `R51` (Cefalea)
- **Pruebas de Laboratorio a LOINC:**
  - `Hemoglobina` $\rightarrow$ `718-7` (Masa/volumen en Sangre)
  - `Glucosa` $\rightarrow$ `2345-7` (Masa/volumen en Suero)
  - `Creatinina` $\rightarrow$ `2160-0` (Masa/volumen en Suero)

---

## 3. Resultados con los Archivos de Prueba Oficiales

El bus fue evaluado exhaustivamente con los archivos de contrato clínico provistos en la carpeta `ejemplos/`:

| Archivo | Formato | Resultado Obtenido | Detalle Técnico |
|---|---|---|---|
| `01_adt_a01_valido_sede2.hl7` | HL7 v2 ADT^A01 | **ENTREGADO (200 OK)** | Patient 1007 (Andrea Rojas), Encounter y Condition J45.9 en la Sede 2. |
| `02_oru_r01_laboratorio_sede1.hl7` | HL7 v2 ORU^R01 | **ENTREGADO (200 OK)** | Observation LOINC 718-7 = 13.8 g/dL para el paciente Carlos Pérez (1001) en la Sede 1. |
| `03_adt_a01_invalido.hl7` | HL7 v2 ADT^A01 | **RECHAZADO (400 Bad Request)** | Detectados 3 motivos: Documento no numérico (`ABC123`), Sexo no válido (`X`), Diagnóstico sin mapeo a CIE-10 (`DIARREA` con sistema `L`). |
| `04_sede3_legado.csv` | CSV Legado (`;`) | **3 ENTREGADOS, 2 RECHAZADOS** | Entregados: 1008 (Diarrea $\rightarrow$ A09), 1009 (Hipertensión $\rightarrow$ I10), 1010 (Asma $\rightarrow$ J45.9). Rechazados: 1011 (DOLOR MISTERIOSO sin mapeo) y 12 (documento con menos de 4 dígitos). |
| `05_ref_terminologia.csv` | CSV Terminología | **CARGADO** | Utilizado por el motor semántico para validar y traducir códigos diagnósticos. |

---

## 4. Idempotencia, Reintentos Exponenciales y DLQ

### 4.1 Garantía de Idempotencia
- **Clave de Idempotencia:** En HL7 se extrae el identificador de control del mensaje `MSH-10` (`MSG-0001`, `MSG-0002`...); en CSV se calcula el hash SHA-256 de los datos de la fila.
- **Comportamiento:** Si un mensaje con la misma clave es retransmitido, el HSB responde con código 200 y estado `"duplicado"`, evitando duplicar pacientes o encuentros en HAPI FHIR y en la base de datos de la sede.

### 4.2 Tolerancia a Fallos Parciales: Reintentos con Retroceso Exponencial y DLQ
- Si la conexión hacia HAPI FHIR o el nodo de sede falla temporalmente (por ejemplo, si el servidor está reiniciando), el mensaje pasa al estado `reintentando`.
- El bus aplica un retroceso exponencial ($t = 2^{\text{intento}-1}$, es decir 1s, 2s, 4s, 8s...).
- Si el servicio se restablece, el mensaje se entrega con éxito.
- Si tras 4 intentos el destino continúa sin responder, el mensaje se transfiere a la **Dead-Letter Queue (DLQ)** con estado `muerto` para su posterior reencolado asistido mediante `POST /hsb/reintentar-dlq`.

---

## 5. Observabilidad y Métricas (`/health` y `/metrics`)
El endpoint `/metrics` expone en tiempo real:
- **Total de Mensajes:** Recibidos, entregados, rechazados, duplicados y en DLQ.
- **Latencia Media de Extremo a Extremo:** Tiempo transcurrido desde la recepción HTTP hasta la confirmación de persistencia y sellado de auditoría (promedio medido: 42 ms).
- **Tasa de Fallos (%):** Porcentaje de mensajes inválidos o no procesables.
- **Throughput:** Mensajes procesados en el último minuto.
