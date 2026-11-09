-- ============================================================================
-- 01_schema_comun.sql — Esquema Relacional de Sede Hospitalaria
-- Plataforma Distribuida de Interoperabilidad Clínica (Sincelejo / Cartagena / Corozal)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Tabla de Usuarios / Pacientes
CREATE TABLE IF NOT EXISTS usuario (
    documento_id            BIGINT PRIMARY KEY,
    tipo_documento          VARCHAR(10)  NOT NULL DEFAULT 'CC',
    pais_nacionalidad       VARCHAR(100) DEFAULT 'Colombia',
    nombre_completo         VARCHAR(255) NOT NULL,
    primer_nombre           VARCHAR(100),
    primer_apellido         VARCHAR(100),
    fecha_nacimiento        DATE,
    edad                    INT,
    unidad_edad             VARCHAR(5)   DEFAULT '1',
    sexo                    VARCHAR(10)  NOT NULL, -- 'M', 'F', 'O'
    genero                  VARCHAR(50),
    ocupacion               VARCHAR(100),
    voluntad_anticipada     BOOLEAN      DEFAULT FALSE,
    categoria_discapacidad  VARCHAR(50),
    pais_residencia         VARCHAR(100) DEFAULT 'Colombia',
    municipio_residencia    VARCHAR(100),
    etnia                   VARCHAR(50),
    comunidad_etnica        VARCHAR(100),
    zona_residencia         VARCHAR(50)  DEFAULT 'Urbana',
    fhir_patient_id         VARCHAR(64), -- NULL inicialmente (cobertura 0%)
    created_at              TIMESTAMP    DEFAULT NOW(),
    updated_at              TIMESTAMP    DEFAULT NOW()
);

-- 2. Tabla de Profesionales de Salud
CREATE TABLE IF NOT EXISTS profesional_salud (
    profesional_id          VARCHAR(50) PRIMARY KEY,
    nombre_completo         VARCHAR(255) NOT NULL,
    registro_medico         VARCHAR(50),
    especialidad            VARCHAR(100),
    sede_id                 INT NOT NULL
);

-- 3. Tabla de Atenciones (Encounters)
CREATE TABLE IF NOT EXISTS atencion (
    atencion_id             SERIAL PRIMARY KEY,
    documento_id            BIGINT NOT NULL REFERENCES usuario(documento_id) ON DELETE CASCADE,
    entidad_salud           VARCHAR(255) NOT NULL,
    sede_id                 INT NOT NULL,
    fecha_ingreso           TIMESTAMP NOT NULL DEFAULT NOW(),
    modalidad_entrega       VARCHAR(50) DEFAULT 'Presencial',
    entorno_atencion        VARCHAR(50) DEFAULT 'Ambulatorio',
    via_ingreso             VARCHAR(50) DEFAULT 'Consulta Externa',
    causa_atencion          TEXT,
    fecha_triage            TIMESTAMP,
    clasificacion_triage    VARCHAR(10), -- '1', '2', '3', '4', '5'
    profesional_id          VARCHAR(50) REFERENCES profesional_salud(profesional_id),
    fhir_encounter_id       VARCHAR(64),
    created_at              TIMESTAMP DEFAULT NOW()
);

-- 4. Tabla de Diagnósticos (Conditions - CIE-10)
CREATE TABLE IF NOT EXISTS diagnostico (
    diagnostico_id          SERIAL PRIMARY KEY,
    atencion_id             INT NOT NULL REFERENCES atencion(atencion_id) ON DELETE CASCADE,
    cie10                   VARCHAR(20) NOT NULL,
    descripcion             VARCHAR(255),
    tipo_diagnostico        VARCHAR(50) DEFAULT 'Confirmado',
    fecha_diagnostico       TIMESTAMP DEFAULT NOW(),
    fhir_condition_id       VARCHAR(64)
);

-- 5. Tabla de Tecnologías en Salud / Procedimientos / Observaciones (LOINC)
CREATE TABLE IF NOT EXISTS tecnologia_salud (
    tecnologia_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    atencion_id             INT NOT NULL REFERENCES atencion(atencion_id) ON DELETE CASCADE,
    codigo_tecnologia       VARCHAR(50) NOT NULL,
    descripcion             VARCHAR(255),
    tipo_tecnologia         VARCHAR(50) DEFAULT 'Laboratorio', -- 'Laboratorio', 'Medicamento', 'Procedimiento'
    valor_resultado         VARCHAR(100),
    unidad_medida           VARCHAR(50),
    estado_orden            VARCHAR(50) DEFAULT 'Completado',
    fecha_orden             TIMESTAMP DEFAULT NOW(),
    fhir_observation_id     VARCHAR(64)
);

-- 6. Tabla de Egresos Clínicos
CREATE TABLE IF NOT EXISTS egreso (
    egreso_id               SERIAL PRIMARY KEY,
    atencion_id             INT UNIQUE NOT NULL REFERENCES atencion(atencion_id) ON DELETE CASCADE,
    fecha_egreso            TIMESTAMP NOT NULL DEFAULT NOW(),
    destino_egreso          VARCHAR(100) DEFAULT 'Domicilio',
    diagnostico_muerte      VARCHAR(20),
    condicion_destino       VARCHAR(100) DEFAULT 'Mejorado',
    sello_integridad        VARCHAR(64) -- Hash SHA-256 del evento
);

-- 7. Tabla de Mensajes del Bus (HSB - Idempotencia y Trazabilidad)
CREATE TABLE IF NOT EXISTS mensaje_bus (
    mensaje_id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clave_idempotencia      VARCHAR(128) UNIQUE NOT NULL, -- MSH-10 o SHA-256 del contenido
    formato_origen          VARCHAR(20)  NOT NULL,        -- 'HL7_ADT', 'HL7_ORU', 'CSV'
    sede_origen             INT          NOT NULL,        -- 1, 2, 3
    documento_id            BIGINT,
    contenido_raw           TEXT         NOT NULL,
    estado                  VARCHAR(30)  NOT NULL,        -- 'recibido', 'validado', 'transformado', 'entregado', 'rechazado', 'reintentando', 'muerto', 'duplicado'
    intentos_reintento      INT          DEFAULT 0,
    max_reintentos          INT          DEFAULT 4,
    motivo_rechazo          TEXT,
    fhir_bundle_id          VARCHAR(64),
    created_at              TIMESTAMP    DEFAULT NOW(),
    updated_at              TIMESTAMP    DEFAULT NOW()
);

-- 8. Tabla de Eventos de Auditoría (Cadena de Hash Criptográfico)
CREATE TABLE IF NOT EXISTS evento_auditoria (
    evento_id               SERIAL PRIMARY KEY,
    prev_hash               VARCHAR(64)  NOT NULL, -- Hash del evento anterior (bloque génesis usa 64 ceros)
    hash                    VARCHAR(64)  NOT NULL, -- SHA-256(prev_hash + timestamp + actor + accion + detalle)
    timestamp               TIMESTAMP    NOT NULL DEFAULT NOW(),
    actor                   VARCHAR(100) NOT NULL, -- Documento o usuario
    rol                     VARCHAR(50)  NOT NULL, -- 'paciente', 'admisionista', 'medico', 'auditor', 'sistema_hsb'
    accion                  VARCHAR(100) NOT NULL, -- 'LOGIN', 'CONSULTA_HC', 'INGRESO_HL7', 'REGISTRO_TRIAGE', etc.
    sede_id                 INT,
    recurso_afectado        VARCHAR(100),
    detalle                 TEXT,
    resultado               VARCHAR(30)  NOT NULL  -- 'EXITOSO', 'DENEGADO', 'RECHAZADO', 'ERROR'
);

-- 9. Tabla de Mapeo de Terminologías Clínicas
CREATE TABLE IF NOT EXISTS ref_terminologia (
    codigo_local            VARCHAR(100) PRIMARY KEY,
    sistema_destino         VARCHAR(100) NOT NULL, -- 'CIE-10', 'LOINC'
    codigo_estandar         VARCHAR(50)  NOT NULL,
    descripcion             VARCHAR(255) NOT NULL,
    tipo_terminologia       VARCHAR(50)  NOT NULL  -- 'Diagnostico', 'Laboratorio'
);

-- Índices de Rendimiento
CREATE INDEX IF NOT EXISTS idx_usuario_doc ON usuario(documento_id);
CREATE INDEX IF NOT EXISTS idx_atencion_doc ON atencion(documento_id);
CREATE INDEX IF NOT EXISTS idx_mensaje_bus_idemp ON mensaje_bus(clave_idempotencia);
CREATE INDEX IF NOT EXISTS idx_evento_auditoria_hash ON evento_auditoria(hash);
