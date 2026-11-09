-- ============================================================================
-- 05_terminologia.sql — Tabla de Referencia de Terminologías Clínicas
-- Mapeo de Diagnósticos Locales a CIE-10 y Pruebas a LOINC
-- ============================================================================

INSERT INTO ref_terminologia (codigo_local, sistema_destino, codigo_estandar, descripcion, tipo_terminologia) VALUES
-- Mapeos de Diagnósticos Locales a CIE-10 (Fuente: ejemplos/05_ref_terminologia.csv)
('DIARREA', 'CIE-10', 'A09', 'Diarrea y gastroenteritis de presunto origen infeccioso', 'Diagnostico'),
('HIPERTENSION', 'CIE-10', 'I10', 'Hipertensión esencial (primaria)', 'Diagnostico'),
('DIABETES', 'CIE-10', 'E11.9', 'Diabetes mellitus tipo 2 sin mención de complicación', 'Diagnostico'),
('ASMA', 'CIE-10', 'J45.9', 'Asma no especificada', 'Diagnostico'),
('INFECCION URINARIA', 'CIE-10', 'N39.0', 'Infección de vías urinarias sitio no especificado', 'Diagnostico'),
('LUMBAGO', 'CIE-10', 'M54.5', 'Lumbago no especificado', 'Diagnostico'),
('NEUMONIA', 'CIE-10', 'J18.9', 'Neumonía no especificada', 'Diagnostico'),
('CEFALEA', 'CIE-10', 'R51', 'Cefalea', 'Diagnostico'),
('GASTRITIS', 'CIE-10', 'K29.7', 'Gastritis no especificada', 'Diagnostico'),
('FIEBRE', 'CIE-10', 'R50.9', 'Fiebre no especificada', 'Diagnostico'),

-- Códigos CIE-10 directos (admitidos como estándar internacional)
('J45.9', 'CIE-10', 'J45.9', 'Asma no especificada', 'Diagnostico'),
('A09', 'CIE-10', 'A09', 'Diarrea y gastroenteritis', 'Diagnostico'),
('I10', 'CIE-10', 'I10', 'Hipertensión esencial', 'Diagnostico'),
('E11.9', 'CIE-10', 'E11.9', 'Diabetes mellitus tipo 2', 'Diagnostico'),

-- Mapeos de Pruebas de Laboratorio a LOINC
('718-7', 'LOINC', '718-7', 'Hemoglobina [Masa/volumen] en Sangre', 'Laboratorio'),
('HEMOGLOBINA', 'LOINC', '718-7', 'Hemoglobina [Masa/volumen] en Sangre', 'Laboratorio'),
('GLUCOSA', 'LOINC', '2345-7', 'Glucosa [Masa/volumen] en Suero o Plasma', 'Laboratorio'),
('2345-7', 'LOINC', '2345-7', 'Glucosa [Masa/volumen] en Suero o Plasma', 'Laboratorio'),
('CREATININA', 'LOINC', '2160-0', 'Creatinina [Masa/volumen] en Suero o Plasma', 'Laboratorio'),
('2160-0', 'LOINC', '2160-0', 'Creatinina [Masa/volumen] en Suero o Plasma', 'Laboratorio')
ON CONFLICT (codigo_local) DO UPDATE SET
    sistema_destino = EXCLUDED.sistema_destino,
    codigo_estandar = EXCLUDED.codigo_estandar,
    descripcion = EXCLUDED.descripcion;
