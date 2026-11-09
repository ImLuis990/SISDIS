# Fase 1: Análisis, Modelado UML y Diseño de Arquitectura

**Proyecto:** Plataforma Distribuida de Interoperabilidad Clínica Multi-Sede  
**Asignatura:** Sistemas Distribuidos  
**Institución:** Corporación Universitaria Antonio José de Sucre  
**Equipo de Desarrollo:**
- Luis Fernando Rios Barboza (luis.rios@corposucre.edu.co)
- Jaime Andrés Villarreal Parra (jaime.villarreal@corposucre.edu.co)  
**Docente:** Ing. Jaider Enrique Reyes Herazo  
**Fecha:** Noviembre de 2026

---

## 1. Resumen Ejecutivo (Abstract)
El fraccionamiento de la información clínica en redes de Instituciones Prestadoras de Salud (IPS) heterogéneas representa un reto crítico para la continuidad asistencial y la toma de decisiones médicas. Este proyecto diseña, implementa y despliega una plataforma distribuida de interoperabilidad clínica que integra tres sedes hospitalarias regionales (Sincelejo, Cartagena y Corozal), preservando sus sistemas legados y unificando sus historias clínicas bajo el estándar internacional HL7® FHIR® R4. La arquitectura incorpora un Bus de Servicios de Salud (HSB) desarrollado con FastAPI para la ingesta de mensajes HL7 v2 (ADT^A01 y ORU^R01) y archivos CSV tabulares, garantizando validación sintáctico-semántica, idempotencia persistente por clave o hash criptográfico, y tolerancia a fallos parciales mediante colas de reintentos con retroceso exponencial y Dead-Letter Queue (DLQ). Los datos clínicos se gestionan a través de tres nodos PostgreSQL distribuidos por sede y un servidor HAPI FHIR central. El sistema proporciona control de acceso basado en roles (RBAC) con JWT para cuatro perfiles (Paciente, Admisionista, Médico y Auditor), un libro de auditoría encadenado por hash SHA-256 a prueba de manipulaciones, y cuatro vistas operativas orientadas al usuario. Las pruebas demuestran una degradación grácil ante caídas de sedes, resolución de consultas unificadas en menos de 120 ms y detección inmediata de alteraciones de auditoría.

---

## 2. Introducción y Planteamiento del Problema
En el contexto del sistema de salud colombiano y latinoamericano, es frecuente que los pacientes sean atendidos en múltiples sedes hospitalarias de una misma red asistencial. Cada sede suele operar sistemas de información hospitalaria (HIS) o registros médicos electrónicos (EMR) independientes y heredados (como Meditech, Servinte o desarrollos propietarios locales), almacenando bases de datos aisladas y emitiendo registros en formatos divergentes (HL7 v2.x en texto delimitado, archivos planos CSV o esquemas relacionales tradicionales).

Esta fragmentación genera historias clínicas dispersas, duplicidad de pruebas de laboratorio diagnósticas, demoras en urgencias y riesgos severos para la seguridad del paciente. Reemplazar todos los sistemas legados por una única solución monolítica es inviable técnica y financieramente. Por tanto, la solución requiere una arquitectura distribuida de interoperabilidad que funcione como puente middleware, transformando y normalizando los datos a recursos estándar FHIR R4 sin interrumpir la operación local de las sedes.

---

## 3. Objetivos

### 3.1 Objetivo General
Construir, desplegar y evaluar una plataforma distribuida de interoperabilidad clínica basada en un Bus de Servicios de Salud (HSB) y el estándar FHIR R4, que unifique de manera transparente y resiliente la historia clínica de pacientes atendidos en tres sedes regionales (Sincelejo, Cartagena y Corozal) conservando sus bases de datos legadas.

### 3.2 Objetivos Específicos
1. **Normalización Semántica:** Implementar un motor de transformación e ingesta en el HSB capaz de recibir mensajes HL7 v2 (ADT^A01 y ORU^R01) y archivos CSV legados, validando su estructura y mapeando diagnósticos locales a CIE-10 y pruebas a LOINC dentro de un Bundle FHIR R4 válido.
2. **Distribución y Tolerancia a Fallos:** Configurar un esquema de datos distribuido en tres nodos PostgreSQL (uno por sede), implementando un middleware de consulta unificada que tolere la caída total de una sede respondiendo en modo degradado sin suspender el servicio.
3. **Idempotencia y Resiliencia en Mensajería:** Garantizar que el reenvío de un mismo mensaje clínico no genere duplicados en el repositorio FHIR ni en las bases de datos de las sedes, gestionando fallos transitorios mediante reintentos con retroceso exponencial y cola de mensajes muertos (DLQ).
4. **Seguridad, Trazabilidad y Visualización:** Asegurar el acceso mediante autenticación JWT y roles estrictos (Paciente, Admisionista, Médico y Reporte de HC/Auditor), respaldado por un registro de auditoría encadenado por hash SHA-256 con verificador automático de integridad criptográfica.

---

## 4. Marco Teórico y Conceptual

### 4.1 Marco Teórico
- **Sistemas Distribuidos y Transparencia:** Un sistema distribuido es una colección de componentes autónomos ubicados en diferentes máquinas que se comunican mediante paso de mensajes, presentándose ante los usuarios como un sistema coherente único (Coulouris et al., 2012). En este proyecto se busca transparencia de localización, acceso y concurrencia.
- **Teorema CAP (Brewer, 2000):** Postula que en presencia de una partición de red ($P$), un sistema distribuido solo puede garantizar Consistencia ($C$) o Disponibilidad ($A$). Nuestra arquitectura prioriza **Disponibilidad y Tolerancia a Particiones (AP)** en la consulta unificada (si la Sede Cartagena cae, Sincelejo y Corozal siguen atendiendo y reportan el estado degradado), mientras que garantiza **Consistencia Fuerte y Atomicidad (ACID)** localmente en cada nodo de sede.
- **Propiedades ACID:** Atomicidad, Consistencia, Aislamiento y Durabilidad. Cada transacción clínica que involucra la creación de un paciente, su atención y diagnóstico en una sede se ejecuta bajo una transacción atómica; si ocurre un fallo a mitad de la operación, se ejecuta un rollback total impidiendo inconsistencias.
- **Estándares de Interoperabilidad en Salud:**
  - **HL7 v2.x:** Estándar de mensajería tradicional basado en sintaxis delimitada por barras verticales (`|`) y sombreritos (`^`). Modela eventos del mundo real (ADT para admisión y egreso, ORU para resultados observacionales).
  - **HL7® FHIR® R4:** Estándar moderno basado en recursos granulares modulares orientados a la web RESTful (JSON/XML), permitiendo modelar pacientes (`Patient`), encuentros (`Encounter`), condiciones clínicas (`Condition`) y observaciones analíticas (`Observation`) agrupados en colecciones deterministas (`Bundle` tipo transaction).
- **Bus de Servicios de Salud (HSB):** Patrón middleware arquitectónico especializado en integrar sistemas heterogéneos de salud, desacoplando emisores y receptores, y proveyendo enrutamiento, mediación de formatos, validación sintáctica y reintentos automáticos.

### 4.2 Marco Conceptual
- **Idempotencia:** Propiedad de una operación donde el resultado tras ser ejecutada múltiples veces con los mismos parámetros es idéntico al obtenido tras la primera ejecución ($f(f(x)) = f(x)$). En el HSB, se implementa utilizando el campo `MSH-10` o el hash SHA-256 del contenido como clave única persistida en base de datos.
- **Dead-Letter Queue (DLQ):** Cola secundaria donde se almacenan mensajes que no pudieron ser procesados exitosamente tras agotar la cuota máxima de reintentos (4 intentos), permitiendo inspección forense y reencolado asistido.
- **Auditoría Encadenada por Hash (Hash-Chained Log):** Estructura de datos inmutable donde cada registro $N$ contiene un hash calculado criptográficamente a partir del hash del registro anterior $N-1$ y el contenido del evento actual: $\text{Hash}_N = \text{SHA-256}(\text{Hash}_{N-1} + \text{Payload}_N)$. Cualquier intento de modificar o borrar un registro histórico invalida la cadena subsecuente de forma inmediata.

---

## 5. Modelado UML

La especificación del sistema cuenta con 4 diagramas UML normalizados:

### 5.1 Diagrama de Casos de Uso
- **Actores:** Paciente, Admisionista, Médico, Sistema Sede Legado (HIS) y Auditor.
- **Casos de Uso Centrales:** Ingesta de mensajes HL7/CSV, normalización FHIR R4, enrutamiento a sedes, consulta de historia unificada multi-sede, admisión con triage, registro diagnóstico CIE-10, órdenes médicas y egreso clínico, descarga de Bundle FHIR, trazabilidad de accesos y verificación de auditoría.
- **Archivo Fuente:** [`casos_de_uso.puml`](file:///home/luis/Desktop/SISDIS/docs/uml/casos_de_uso.puml)
- **Imagen Vectorial:** [`casos_de_uso.svg`](file:///home/luis/Desktop/SISDIS/docs/uml/casos_de_uso.svg)

### 5.2 Diagrama de Secuencia
- **Flujo:** Mensaje HL7 v2 ADT^A01 emitido por la Sede Cartagena hacia el HSB, validación de reglas e idempotencia, bifurcación ante rechazo o duplicado, transformación a Bundle FHIR R4, transacción PUT en HAPI FHIR, inserción en nodo local PostgreSQL y generación de sello en auditoría encadenada.
- **Archivo Fuente:** [`secuencia.puml`](file:///home/luis/Desktop/SISDIS/docs/uml/secuencia.puml)
- **Imagen Vectorial:** [`secuencia.svg`](file:///home/luis/Desktop/SISDIS/docs/uml/secuencia.svg)

### 5.3 Diagrama de Clases
- **Entidades:** `Usuario`, `Atencion`, `Diagnostico`, `TecnologiaSalud`, `Egreso`, `ProfesionalSalud`, `MensajeBus`, `EventoAuditoria`, `RefTerminologia`, `FhirBundle` y `SedeConfig`.
- **Relaciones:** Composiciones, asociaciones y dependencias entre la capa clínica relacional y los modelos middleware y FHIR.
- **Archivo Fuente:** [`clases.puml`](file:///home/luis/Desktop/SISDIS/docs/uml/clases.puml)
- **Imagen Vectorial:** [`clases.svg`](file:///home/luis/Desktop/SISDIS/docs/uml/clases.svg)

### 5.4 Diagrama de Estados
- **Estados del Mensaje en el HSB:** `RECIBIDO` $\rightarrow$ `DUPLICADO` / `VALIDANDO` $\rightarrow$ `RECHAZADO` / `TRANSFORMADO` $\rightarrow$ `ENVIANDO_FHIR` $\rightarrow$ `PERSISTIENDO_SEDE` $\rightarrow$ `ENTREGADO` / `REINTENTANDO` $\rightarrow$ `MUERTO` (DLQ).
- **Archivo Fuente:** [`estados.puml`](file:///home/luis/Desktop/SISDIS/docs/uml/estados.puml)
- **Imagen Vectorial:** [`estados.svg`](file:///home/luis/Desktop/SISDIS/docs/uml/estados.svg)

---

## 6. Arquitectura del Sistema y Justificación Técnica

### 6.1 Diagrama de Arquitectura
- **Archivo Fuente:** [`arquitectura.puml`](file:///home/luis/Desktop/SISDIS/docs/uml/arquitectura.puml)
- **Imagen Vectorial:** [`arquitectura.svg`](file:///home/luis/Desktop/SISDIS/docs/uml/arquitectura.svg)

### 6.2 Tabla de Justificación de Componentes

| Componente | Requisito Cubierto | Por qué lo elegimos frente a las alternativas |
|---|---|---|
| **Health Service Bus (HSB en FastAPI)** | RF1, RF3 | **Frente a Mirth Connect / Apache Camel:** Proporciona un control determinista de bajo nivel sobre validaciones complejas, cálculo de hashes SHA-256 para auditoría, reintentos asíncronos nativos, tipado estático con Pydantic y bajo consumo de memoria RAM (< 80 MB frente a > 1 GB en JVM). |
| **Servidor HAPI FHIR R4** | RF2, RF6 | **Frente a FHIR Server casero:** HAPI FHIR es la implementación de referencia global con soporte completo del estándar FHIR R4.0.1, motor de validación semántica `$validate`, transacciones atómicas PUT y capacidad de exportación conforme a los estándares internacionales. |
| **3 Nodos PostgreSQL Distribuidos** | RF4, RNF | **Frente a base de datos única centralizada:** Reproduce fielmente el escenario real de sedes hospitalarias aisladas geográficamente (Sincelejo, Cartagena, Corozal). Permite demostrar la tolerancia a fallos parciales: si un contenedor se detiene (`docker stop`), los demás siguen operando. |
| **Autenticación JWT con RBAC** | RF5 | **Frente a Basic Auth / Sesiones tradicionales:** Los JSON Web Tokens son autocontenidos, permitiendo verificar identidad y roles (`paciente`, `admisionista`, `medico`, `auditor`) sin consultas recurrentes a un servidor de sesiones central, facilitando la escalabilidad horizontal. |
| **Auditoría Encadenada SHA-256** | RF5 | **Frente a logs en texto plano:** Los logs tradicionales pueden ser alterados o borrados por administradores comprometidos. La cadena de hashes criptográficos emula una blockchain privada ligera sin la sobrecarga computacional de consenso distribuido, garantizando no repudio. |
| **Frontend Web 4 Vistas** | RF6 | **Frente a interfaces de consola o tablero único:** Ofrece vistas desacopladas y específicas para cada actor de salud, protegiendo datos sensibles (admisionistas no ven diagnósticos clínicos) y facilitando la exportación de reportes clínicos y bundles FHIR. |

---

## 7. Tabla de Mapeo de Campos Origen a Recursos FHIR R4

A continuación se detallan 20 campos de ingesta (desde mensajes HL7 v2 y archivos CSV legados) mapeados a las tablas relacionales locales y a sus correspondientes recursos FHIR R4:

| # | Origen (HL7 v2 / CSV) | Tabla Relacional | Campo Relacional | Recurso FHIR R4 | Elemento FHIR R4 | Tipo de Dato |
|---|---|---|---|---|---|---|
| 1 | `PID-3.1` / `documento` | `usuario` | `documento_id` | `Patient` | `identifier[0].value` | `string` |
| 2 | Constante `'HIS'` | `usuario` | `tipo_documento` | `Patient` | `identifier[0].system` | `uri` |
| 3 | `PID-5.1` / Apellidos en `nombre` | `usuario` | `nombre_completo` | `Patient` | `name[0].family` | `string` |
| 4 | `PID-5.2` / Nombres en `nombre` | `usuario` | `nombre_completo` | `Patient` | `name[0].given[0]` | `string` |
| 5 | `PID-7` / `nacimiento` | `usuario` | `fecha_nacimiento` | `Patient` | `birthDate` | `date` |
| 6 | `PID-8` / `sexo` | `usuario` | `sexo` | `Patient` | `gender` | `code` (male/female/other) |
| 7 | Clave determinista | `usuario` | `fhir_patient_id` | `Patient` | `id` (`pac-<documento>`) | `id` |
| 8 | `PV1-19` / ID Visita | `atencion` | `atencion_id` | `Encounter` | `id` (`enc-<id>`) | `id` |
| 9 | `PV1-2` / Modalidad | `atencion` | `modalidad_entrega` | `Encounter` | `class.code` (AMB, EMER, IMP) | `Coding` |
| 10 | `PV1-44` / `fecha` | `atencion` | `fecha_ingreso` | `Encounter` | `period.start` | `dateTime` |
| 11 | `MSH-4` / Parámetro `sede` | `atencion` | `entidad_salud` | `Encounter` | `serviceProvider.display` | `string` |
| 12 | `PV1-7.1` / `profesional` | `atencion` | `profesional_id` | `Encounter` | `participant[0].individual` | `Reference` |
| 13 | `triage` (1 a 5) | `atencion` | `clasificacion_triage` | `Encounter` | `priority.coding[0].code` | `code` |
| 14 | `DG1-3.1` / Mapeo `dx_local` | `diagnostico` | `cie10` | `Condition` | `code.coding[0].code` | `code` (CIE-10) |
| 15 | `DG1-3.2` / `descripcion` | `diagnostico` | `descripcion` | `Condition` | `code.coding[0].display` | `string` |
| 16 | `DG1-5` / `fecha` | `diagnostico` | `fecha_diagnostico` | `Condition` | `recordedDate` | `dateTime` |
| 17 | `OBX-3.1` / Código prueba | `tecnologia_salud` | `codigo_tecnologia` | `Observation` | `code.coding[0].code` | `code` (LOINC) |
| 18 | `OBX-3.2` / Nombre prueba | `tecnologia_salud` | `descripcion` | `Observation` | `code.coding[0].display` | `string` |
| 19 | `OBX-5` / Valor numérico | `tecnologia_salud` | `valor_resultado` | `Observation` | `valueQuantity.value` | `decimal` |
| 20 | `OBX-6` / Unidad medida | `tecnologia_salud` | `unidad_medida` | `Observation` | `valueQuantity.unit` | `string` |

---

## 8. Criterios de Aceptación Cumplidos (Fase 1)
- [x] Repositorio estructurado en carpetas normalizadas (`docs/`, `infra/`, `hsb/`, `fhir/`, `db/`, `app/`, `tests/`, `ejemplos/`).
- [x] 4 diagramas UML elaborados en fuente editable PlantUML (`.puml`) y exportados a imágenes vectoriales SVG de alta fidelidad.
- [x] Diagrama de arquitectura general y tabla de justificación de decisiones tecnológicas.
- [x] Tabla de mapeo de 20 campos origen a recursos estándar FHIR R4.
- [x] Coherencia estricta entre actores de casos de uso, entidades del diagrama de clases, pasos de la secuencia y estados del bus.
