# Matriz de Interoperabilidad: 57 Campos de la Resolución 866 de 2021 (MinSalud Colombia)

Esta tabla establece la correspondencia formal de los **57 elementos de datos clínicos del Resumen Digital de Atención (RDA)** frente al esquema relacional multi-sede y los recursos HL7 FHIR R4.

| # | Elemento de Dato Clínico (Resolución 866/2021) | Tabla Relacional | Campo en Base de Datos | Recurso FHIR R4 Mapeado | Formato / Catálogo Estándar |
|---|---|---|---|---|---|
| 1 | Tipo de identificación del usuario | `usuario` | `tipo_documento` | `Patient.identifier[0].type` | CÓDIGO (CC, TI, RC, CE, PA) |
| 2 | Número de identificación del usuario | `usuario` | `documento_id` | `Patient.identifier[0].value` | TEXTO / NÚMERO |
| 3 | Primer apellido del usuario | `usuario` | `primer_apellido` | `Patient.name[0].family` | TEXTO |
| 4 | Segundo apellido del usuario | `usuario` | `nombre_completo` | `Patient.name[0].family (ext)` | TEXTO |
| 5 | Primer nombre del usuario | `usuario` | `primer_nombre` | `Patient.name[0].given[0]` | TEXTO |
| 6 | Segundo nombre del usuario | `usuario` | `nombre_completo` | `Patient.name[0].given[1]` | TEXTO |
| 7 | Fecha de nacimiento | `usuario` | `fecha_nacimiento` | `Patient.birthDate` | DATE (AAAA-MM-DD) |
| 8 | Sexo biológico | `usuario` | `sexo` | `Patient.gender` | male | female | other |
| 9 | Identidad de género | `usuario` | `genero` | `Patient.extension(gender-identity)` | CÓDIGO |
| 10 | Nacionalidad | `usuario` | `pais_nacionalidad` | `Patient.extension(nationality)` | ISO-3166 (Colombia) |
| 11 | País de residencia habitual | `usuario` | `pais_residencia` | `Patient.address.country` | ISO-3166 (Colombia) |
| 12 | Municipio de residencia habitual | `usuario` | `municipio_residencia` | `Patient.address.city` | DIVIPOLA |
| 13 | Zona de residencia habitual | `usuario` | `zona_residencia` | `Patient.address.extension(zone)` | Urbana | Rural |
| 14 | Pertenencia étnica | `usuario` | `etnia` | `Patient.extension(ethnicity)` | CÓDIGO MINSALUD |
| 15 | Comunidad o pueblo étnico | `usuario` | `comunidad_etnica` | `Patient.extension(ethnic-group)` | TEXTO |
| 16 | Categoría de discapacidad | `usuario` | `categoria_discapacidad` | `Patient.extension(disability)` | CÓDIGO |
| 17 | Voluntad anticipada | `usuario` | `voluntad_anticipada` | `Consent / Patient.extension` | BOOLEANO (true/false) |
| 18 | Código de habilitación prestador (REPS) | `atencion` | `entidad_salud` | `Organization.identifier / serviceProvider` | REPS 12 dígitos |
| 19 | Sede del prestador de servicios | `atencion` | `sede_id` | `Location.name / Encounter.location` | CÓDIGO SEDE (1, 2, 3) |
| 20 | Tipo de identificación del profesional | `profesional_salud` | `profesional_id` | `Practitioner.identifier.type` | CÓDIGO |
| 21 | Número de identificación profesional | `profesional_salud` | `profesional_id` | `Practitioner.identifier.value` | TEXTO |
| 22 | Nombres y apellidos del profesional | `profesional_salud` | `nombre_completo` | `Practitioner.name.text` | TEXTO |
| 23 | Identificador de la atención asistencial | `atencion` | `atencion_id` | `Encounter.id` | ID determinista (enc-<id>) |
| 24 | Fecha y hora de inicio de atención | `atencion` | `fecha_ingreso` | `Encounter.period.start` | DATETIME ISO-8601 |
| 25 | Fecha y hora de egreso de atención | `egreso` | `fecha_egreso` | `Encounter.period.end` | DATETIME ISO-8601 |
| 26 | Modalidad de atención | `atencion` | `modalidad_entrega` | `Encounter.class` | Presencial | Telemedicina |
| 27 | Entorno de la atención | `atencion` | `entorno_atencion` | `Encounter.serviceType` | Ambulatorio | Hospitalario | Urgencias |
| 28 | Vía de ingreso a la atención | `atencion` | `via_ingreso` | `Encounter.hospitalization.admitSource` | Consulta Externa | Urgencias | Remitido |
| 29 | Causa que motiva la atención | `atencion` | `causa_atencion` | `Encounter.reasonCode` | Enfermedad general | Accidente |
| 30 | Fecha y hora del triage | `atencion` | `fecha_triage` | `Encounter.extension(triage-date)` | DATETIME ISO-8601 |
| 31 | Clasificación del triage | `atencion` | `clasificacion_triage` | `Encounter.priority` | Nivel I a V (1, 2, 3, 4, 5) |
| 32 | Estado del encuentro asistencial | `atencion` | `created_at` | `Encounter.status` | in-progress | finished |
| 33 | Código del diagnóstico principal | `diagnostico` | `cie10` | `Condition.code.coding[0].code` | CIE-10 (ej. J45.9, I10) |
| 34 | Descripción del diagnóstico principal | `diagnostico` | `descripcion` | `Condition.code.coding[0].display` | TEXTO ESTÁNDAR |
| 35 | Tipo de diagnóstico principal | `diagnostico` | `tipo_diagnostico` | `Condition.clinicalStatus` | Presuntivo | Confirmado |
| 36 | Fecha del diagnóstico clínico | `diagnostico` | `fecha_diagnostico` | `Condition.recordedDate` | DATE / DATETIME |
| 37 | Código diagnóstico relacionado 1 | `diagnostico` | `cie10_rel1` | `Condition.code (secondary)` | CIE-10 |
| 38 | Código diagnóstico relacionado 2 | `diagnostico` | `cie10_rel2` | `Condition.code (secondary)` | CIE-10 |
| 39 | Antecedente patológico personal | `diagnostico` | `antecedentes` | `Condition (category: problem-list-item)` | CIE-10 / SNOMED CT |
| 40 | Antecedente farmacológico | `tecnologia_salud` | `antecedente_farmacologico` | `MedicationStatement.medication` | Código IUM / CUM |
| 41 | Antecedente alérgico | `usuario` | `alergias` | `AllergyIntolerance.code` | SNOMED CT |
| 42 | Código de la tecnología en salud / lab | `tecnologia_salud` | `codigo_tecnologia` | `Observation.code.coding[0].code` | LOINC (ej. 718-7, 2345-7) / CUPS |
| 43 | Descripción de la tecnología en salud | `tecnologia_salud` | `descripcion` | `Observation.code.coding[0].display` | TEXTO ESTÁNDAR |
| 44 | Fecha de realización del paraclínico | `tecnologia_salud` | `fecha_solicitud` | `Observation.effectiveDateTime` | DATETIME ISO-8601 |
| 45 | Resultado cuantitativo de la medición | `tecnologia_salud` | `valor_resultado` | `Observation.valueQuantity.value` | DECIMAL (ej. 13.8) |
| 46 | Unidad de medida estandarizada | `tecnologia_salud` | `unidad_medida` | `Observation.valueQuantity.unit` | UCUM (ej. g/dL, mg/dL) |
| 47 | Interpretación clínica del resultado | `tecnologia_salud` | `interpretacion` | `Observation.interpretation` | Normal | Alto | Bajo |
| 48 | Rango de referencia - límite inferior | `tecnologia_salud` | `rango_min` | `Observation.referenceRange.low` | DECIMAL |
| 49 | Rango de referencia - límite superior | `tecnologia_salud` | `rango_max` | `Observation.referenceRange.high` | DECIMAL |
| 50 | Procedimiento quirúrgico / terapéutico | `tecnologia_salud` | `codigo_procedimiento` | `Procedure.code.coding[0].code` | CUPS (Clasificación Única Proc) |
| 51 | Destino del usuario al egreso | `egreso` | `destino_usuario` | `Encounter.hospitalization.dischargeDisposition` | Domicilio | Remisión | Hospitalización |
| 52 | Diagnóstico principal de egreso | `egreso` | `diagnostico_principal_egreso` | `Condition / Encounter.diagnosis` | CIE-10 |
| 53 | Fecha y hora del egreso asistencial | `egreso` | `fecha_egreso` | `Encounter.period.end` | DATETIME ISO-8601 |
| 54 | Identificación del profesional de egreso | `egreso` | `profesional_egreso_id` | `Practitioner.identifier.value` | TEXTO |
| 55 | Plan de manejo y recomendaciones | `egreso` | `plan_manejo` | `CarePlan.description` | TEXTO |
| 56 | Sello criptográfico digital de atención | `mensaje_bus` | `sello_integridad_sha256` | `Provenance.signature / hash` | HASH SHA-256 (64 hex) |
| 57 | Documento clínico consolidado (RDA) | `mensaje_bus` | `fhir_bundle_json` | `Bundle (transaction / document)` | BUNDLE FHIR R4 JSON |
