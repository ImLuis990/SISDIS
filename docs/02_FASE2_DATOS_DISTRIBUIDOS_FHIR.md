# Fase 2: Capa de Datos Distribuidos y Normalización FHIR R4

**Proyecto:** Plataforma Distribuida de Interoperabilidad Clínica Multi-Sede  
**Asignatura:** Sistemas Distribuidos  
**Institución:** Corporación Universitaria Antonio José de Sucre  
**Equipo de Desarrollo:**
- Luis Fernando Rios Barboza (luis.rios@corposucre.edu.co)
- Jaime Andrés Villarreal Parra (jaime.villarreal@corposucre.edu.co)  
**Docente:** Ing. Jaider Enrique Reyes Herazo  
**Fecha:** Noviembre de 2026

---

## 1. Estado del Arte en Interoperabilidad y Almacenamiento Clínico
En la literatura actual sobre interoperabilidad en salud se destacan múltiples arquitecturas de mediación y persistencia:
- **HAPI FHIR Server (Smile CDR):** Servidor de referencia de código abierto en Java para HL7 FHIR. Implementa el estándar RESTful completo, validadores de perfiles mediante `$validate` y transacciones atómicas tipo Bundle.
- **Mirth Connect (NextGen Healthcare):** Motor de integración tradicional para canales HL7 v2 y enrutamiento punto a punto. Aunque robusto en mensajería clásica, presenta un alto consumo de memoria RAM y curva de aprendizaje elevada para lógica moderna basada en microservicios y criptografía.
- **OpenHIM (Open Health Information Mediator):** Middleware diseñado para interoperabilidad en salud global, enfocado en orquestar peticiones, mediación de autenticación y auditoría.
- **Apache Camel:** Framework de patrones de integración empresarial (EIP) versátil pero genérico, requiriendo módulos adicionales para soporte semántico en salud (CIE-10, LOINC).

Frente a estas alternativas, este proyecto implementa un bus ligero HSB en Python/FastAPI con un servidor HAPI FHIR R4 central y almacenamiento distribuido en tres nodos PostgreSQL (uno por sede), optimizando el rendimiento, la auditabilidad inmutable y el aislamiento de fallas.

---

## 2. Solución Propuesta para la Capa de Datos

### 2.1 Estrategia de Distribución y Análisis CAP
Se configuró una arquitectura de tres nodos PostgreSQL independientes:
- **Sede 1 (Sincelejo):** `pg_sede1` (Puerto host 5431, base de datos `historia_clinica_sede1`).
- **Sede 2 (Cartagena):** `pg_sede2` (Puerto host 5432, base de datos `historia_clinica_sede2`).
- **Sede 3 (Corozal):** `pg_sede3` (Puerto host 5433, base de datos `historia_clinica_sede3`).

**Justificación frente a Citus o Fragmentación por Documento:**
En el mundo hospitalario real, cada sede conserva la custodia legal y operativa de los datos que genera en sus propias instalaciones. Un esquema de un nodo por sede respeta la soberanía local de los sistemas legados.

**Compromiso según el Teorema CAP:**
- **Persistencia Local (ACID):** Cada sede garantiza Consistencia Fuerte y Atomicidad total en sus transacciones clínicas locales (inserción conjunta de paciente, atención y diagnóstico).
- **Consulta Unificada (AP - Alta Disponibilidad y Tolerancia a Particiones):** Cuando el middleware consulta la historia unificada de un paciente en las tres sedes, si una de las sedes experimenta una partición o caída de red (`docker stop`), el sistema prioriza la **Disponibilidad**: responde inmediatamente con la información de las sedes supervivientes y marca la sede afectada como `no disponible (degradado)`.

### 2.2 Resolución de Identidad de Pacientes (MPI Simplificado)
- **Regla de Coincidencia Primaria:** Documento de identidad numérico exacto (`documento_id`) y tipo de documento (`CC`, `TI`, `CE`).
- **Análisis de Falsos Positivos y Falsos Negativos:**
  - *Falsos Positivos:* Podrían ocurrir si dos sedes registran por error humano a pacientes diferentes con el mismo número de cédula pero distinto tipo documental, o por un error de digitación en el teclado. La plataforma mitiga esto validando en el HSB que el documento sea estrictamente numérico y cotejando la fecha de nacimiento.
  - *Falsos Negativos:* Ocurren cuando el mismo paciente presenta cédula en una sede y tarjeta de identidad previa en otra. En el diseño se documenta la necesidad futura de un motor probabilístico tipo Fellegi-Sunter sobre nombres y fonemas (Soundex/Metaphone).

---

## 3. Demostración de Transacciones Atómicas (ACID)
Para garantizar que nunca queden registros clínicos a medias o usuarios huérfanos sin atención asociada, se implementó el módulo [`db/demo_acid.py`](file:///home/luis/Desktop/SISDIS/db/demo_acid.py).

### Evidencia de la Ejecución de Prueba:
```text
============================================================
DEMOSTRACIÓN DE ATOMICIDAD (ACID) EN TRANSACCIONES CLÍNICAS
============================================================
[ANTES] Documento 999999: 0 usuarios, 0 atenciones en BD.

[PROCESO] Iniciando transacción con error forzado a mitad de ejecución...
[ERROR CAPTURADO] ERROR_FORZADO: Fallo de integridad inducido a mitad de transacción
[ACCIÓN DISPARADA] ROLLBACK_EJECUTADO

[DESPUÉS] Documento 999999: 0 usuarios, 0 atenciones en BD.

>>> RESULTADO ACID: ÉXITO TOTAL.
    El rollback impidió que el usuario quedara registrado huérfano.
============================================================
```

---

## 4. Normalizador a FHIR R4
El módulo [`fhir/normalizador.py`](file:///home/luis/Desktop/SISDIS/fhir/normalizador.py) implementa la transformación reproducible hacia el estándar internacional FHIR R4:
- **IDs Deterministas:** Se emplea el patrón `pac-<documento_id>`, `enc-<atencion_id>`, `cond-<diagnostico_id>` y `obs-<tecnologia_id>`. Esto elimina el riesgo de colisiones y duplicidades accidentales.
- **Empaquetado en Bundle Transaction con PUT:** Cada recurso dentro del Bundle especifica:
  ```json
  "request": {
    "method": "PUT",
    "url": "Patient/pac-1007"
  }
  ```
  Esto garantiza que el reenvío de un mismo mensaje actualice el recurso existente sin crear duplicados.
- **Pruebas Unitarias:** 7 pruebas automatizadas en [`tests/test_normalizador_fhir.py`](file:///home/luis/Desktop/SISDIS/tests/test_normalizador_fhir.py) con 100% de aprobación.

---

## 5. Criterios de Aceptación Cumplidos (Fase 2)
- [x] Scripts SQL de creación de tablas relacionales y carga sintética en 3 sedes (`01_schema_comun.sql`, `02_datos_sede1.sql`, `03_datos_sede2.sql`, `04_datos_sede3.sql`, `05_terminologia.sql`).
- [x] Paciente de prueba multi-sede (Carlos Pérez, CC 1001) presente en Sincelejo, Cartagena y Corozal con atenciones y pruebas independientes.
- [x] Normalizador FHIR R4 determinista con pruebas unitarias de casos válidos e inválidos.
- [x] Demostración empírica de atomicidad transaccional (ACID) con reversión automática (`ROLLBACK`).
