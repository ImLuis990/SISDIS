-- ============================================================================
-- 03_datos_sede2.sql — Datos Sintéticos Iniciales: Sede 2 (Cartagena)
-- fhir_patient_id se inicializa en NULL para representar cobertura FHIR inicial de 0%
-- ============================================================================

-- Profesional de Salud Sede 2
INSERT INTO profesional_salud (profesional_id, nombre_completo, registro_medico, especialidad, sede_id) VALUES
('MED-02', 'Dr. Mateo Ruiz', 'RM-889900-BOL', 'Neumología', 2),
('MED-04', 'Dra. Patricia Silva', 'RM-112233-BOL', 'Urgenciología', 2)
ON CONFLICT (profesional_id) DO NOTHING;

-- Pacientes iniciales Sede 2 (Cartagena)
-- Nótese: El paciente 1001 también tiene registro en Sede 2, permitiendo demostrar la consulta unificada multi-sede.
INSERT INTO usuario (documento_id, tipo_documento, nombre_completo, primer_nombre, primer_apellido, fecha_nacimiento, edad, sexo, fhir_patient_id) VALUES
(1001, 'CC', 'Carlos Perez', 'Carlos', 'Perez', '1980-04-12', 46, 'M', NULL),
(1002, 'CC', 'Beatriz Morales Paternina', 'Beatriz', 'Morales', '1975-11-20', 51, 'F', NULL)
ON CONFLICT (documento_id) DO NOTHING;

-- Atenciones Sede 2
INSERT INTO atencion (atencion_id, documento_id, entidad_salud, sede_id, fecha_ingreso, modalidad_entrega, entorno_atencion, via_ingreso, causa_atencion, clasificacion_triage, profesional_id) VALUES
(201, 1001, 'Clínica Mar de Cartagena', 2, '2026-11-06 11:20:00', 'Presencial', 'Ambulatorio', 'Consulta Externa', 'Dolor torácico opresivo y tos seca', '2', 'MED-02'),
(202, 1002, 'Clínica Mar de Cartagena', 2, '2026-11-06 16:45:00', 'Presencial', 'Urgencias', 'Urgencias', 'Crisis hipertensiva con mareo', '2', 'MED-04')
ON CONFLICT (atencion_id) DO NOTHING;

-- Diagnósticos Sede 2
INSERT INTO diagnostico (atencion_id, cie10, descripcion, tipo_diagnostico) VALUES
(201, 'J45.9', 'Asma no especificada', 'Confirmado'),
(202, 'I10', 'Hipertensión esencial (primaria)', 'Confirmado');

-- Tecnologías en Salud Sede 2
INSERT INTO tecnologia_salud (atencion_id, codigo_tecnologia, descripcion, tipo_tecnologia, valor_resultado, unidad_medida) VALUES
(202, '2345-7', 'Glucosa [Masa/volumen] en Suero o Plasma', 'Laboratorio', '108', 'mg/dL');
