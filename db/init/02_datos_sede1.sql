-- ============================================================================
-- 02_datos_sede1.sql — Datos Sintéticos Iniciales: Sede 1 (Sincelejo)
-- fhir_patient_id se inicializa en NULL para representar cobertura FHIR inicial de 0%
-- ============================================================================

-- Profesional de Salud Sede 1
INSERT INTO profesional_salud (profesional_id, nombre_completo, registro_medico, especialidad, sede_id) VALUES
('MED-01', 'Dra. Laura Vega', 'RM-102938-SUC', 'Medicina Interna', 1),
('MED-03', 'Dr. Andrés Castro', 'RM-445566-SUC', 'Medicina General', 1)
ON CONFLICT (profesional_id) DO NOTHING;

-- Pacientes iniciales Sede 1 (Sincelejo)
INSERT INTO usuario (documento_id, tipo_documento, nombre_completo, primer_nombre, primer_apellido, fecha_nacimiento, edad, sexo, fhir_patient_id) VALUES
(1001, 'CC', 'Carlos Perez', 'Carlos', 'Perez', '1980-04-12', 46, 'M', NULL),
(1004, 'CC', 'Elena Ramos Gomez', 'Elena', 'Ramos', '1992-08-15', 34, 'F', NULL)
ON CONFLICT (documento_id) DO NOTHING;

-- Atenciones Sede 1
INSERT INTO atencion (atencion_id, documento_id, entidad_salud, sede_id, fecha_ingreso, modalidad_entrega, entorno_atencion, via_ingreso, causa_atencion, clasificacion_triage, profesional_id) VALUES
(101, 1001, 'Hospital Regional de Sincelejo', 1, '2026-11-05 08:30:00', 'Presencial', 'Urgencias', 'Urgencias', 'Control clínico por anemia y fatiga general', '3', 'MED-01'),
(102, 1004, 'Hospital Regional de Sincelejo', 1, '2026-11-06 14:15:00', 'Presencial', 'Ambulatorio', 'Consulta Externa', 'Cefalea recurrente tensional', '4', 'MED-03')
ON CONFLICT (atencion_id) DO NOTHING;

-- Diagnósticos Sede 1
INSERT INTO diagnostico (atencion_id, cie10, descripcion, tipo_diagnostico) VALUES
(101, 'D50.9', 'Anemia por deficiencia de hierro sin especificación', 'Presuntivo'),
(102, 'R51', 'Cefalea', 'Confirmado');

-- Tecnologías en Salud Sede 1
INSERT INTO tecnologia_salud (atencion_id, codigo_tecnologia, descripcion, tipo_tecnologia, valor_resultado, unidad_medida) VALUES
(101, '718-7', 'Hemoglobina [Masa/volumen] en Sangre', 'Laboratorio', '12.1', 'g/dL');
