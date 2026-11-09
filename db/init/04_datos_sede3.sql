-- ============================================================================
-- 04_datos_sede3.sql — Datos Sintéticos Iniciales: Sede 3 (Corozal)
-- fhir_patient_id se inicializa en NULL para representar cobertura FHIR inicial de 0%
-- ============================================================================

-- Profesional de Salud Sede 3
INSERT INTO profesional_salud (profesional_id, nombre_completo, registro_medico, especialidad, sede_id) VALUES
('MED-01', 'Dra. Laura Vega', 'RM-102938-SUC', 'Medicina Interna', 3),
('MED-05', 'Dr. Fabio Salgado', 'RM-778899-SUC', 'Medicina General', 3)
ON CONFLICT (profesional_id) DO NOTHING;

-- Pacientes iniciales Sede 3 (Corozal)
-- Paciente 1001 completa atenciones en las TRES SEDES (Sincelejo, Cartagena y Corozal)
INSERT INTO usuario (documento_id, tipo_documento, nombre_completo, primer_nombre, primer_apellido, fecha_nacimiento, edad, sexo, fhir_patient_id) VALUES
(1001, 'CC', 'Carlos Perez', 'Carlos', 'Perez', '1980-04-12', 46, 'M', NULL),
(1003, 'CC', 'Jorge Hernandez Vergara', 'Jorge', 'Hernandez', '1968-03-30', 58, 'M', NULL)
ON CONFLICT (documento_id) DO NOTHING;

-- Atenciones Sede 3
INSERT INTO atencion (atencion_id, documento_id, entidad_salud, sede_id, fecha_ingreso, modalidad_entrega, entorno_atencion, via_ingreso, causa_atencion, clasificacion_triage, profesional_id) VALUES
(301, 1001, 'Centro de Salud San Juan de Corozal', 3, '2026-11-07 07:15:00', 'Presencial', 'Ambulatorio', 'Consulta Externa', 'Evaluación de control por lumbalgia mecánica', '4', 'MED-05'),
(302, 1003, 'Centro de Salud San Juan de Corozal', 3, '2026-11-07 09:00:00', 'Presencial', 'Urgencias', 'Urgencias', 'Diarrea aguda y deshidratación leve', '3', 'MED-01')
ON CONFLICT (atencion_id) DO NOTHING;

-- Diagnósticos Sede 3
INSERT INTO diagnostico (atencion_id, cie10, descripcion, tipo_diagnostico) VALUES
(301, 'M54.5', 'Lumbago no especificado', 'Confirmado'),
(302, 'A09', 'Diarrea y gastroenteritis de presunto origen infeccioso', 'Confirmado');

-- Tecnologías en Salud Sede 3
INSERT INTO tecnologia_salud (atencion_id, codigo_tecnologia, descripcion, tipo_tecnologia, valor_resultado, unidad_medida) VALUES
(302, '2160-0', 'Creatinina [Masa/volumen] en Suero o Plasma', 'Laboratorio', '0.9', 'mg/dL');
