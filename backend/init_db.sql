CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE IF NOT EXISTS severity_enum AS ENUM ('critical', 'high', 'moderate', 'low');
CREATE TYPE IF NOT EXISTS alert_level_enum AS ENUM ('red', 'orange', 'yellow');

CREATE TABLE IF NOT EXISTS hospitals (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY,
    hospital_id UUID REFERENCES hospitals(id) ON DELETE SET NULL,
    reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    diagnosis VARCHAR(255) NOT NULL,
    severity severity_enum NOT NULL,
    location GEOMETRY(POINT, 4326) NOT NULL,
    is_confirmed BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS alert_zones (
    id UUID PRIMARY KEY,
    zone_name VARCHAR(255) NOT NULL,
    alert_level alert_level_enum NOT NULL,
    geometry GEOMETRY(POLYGON, 4326) NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS case_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    changed_field VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_cases_location_gist ON cases USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_cases_reported_at_brin ON cases USING BRIN (reported_at);
CREATE INDEX IF NOT EXISTS idx_cases_severity_reported_at ON cases (severity, reported_at DESC);
CREATE INDEX IF NOT EXISTS idx_cases_hospital_id ON cases (hospital_id);
CREATE INDEX IF NOT EXISTS idx_alert_zones_geometry_gist ON alert_zones USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_case_audit_logs_case_id ON case_audit_logs (case_id);
CREATE INDEX IF NOT EXISTS idx_case_audit_logs_changed_at ON case_audit_logs (changed_at DESC);

CREATE OR REPLACE FUNCTION log_case_update() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.hospital_id IS DISTINCT FROM OLD.hospital_id THEN
        INSERT INTO case_audit_logs (id, case_id, changed_field, old_value, new_value, changed_by)
        VALUES (gen_random_uuid(), NEW.id, 'hospital_id', OLD.hospital_id::text, NEW.hospital_id::text, current_setting('app.changed_by', true));
    END IF;
    IF NEW.diagnosis IS DISTINCT FROM OLD.diagnosis THEN
        INSERT INTO case_audit_logs (id, case_id, changed_field, old_value, new_value, changed_by)
        VALUES (gen_random_uuid(), NEW.id, 'diagnosis', OLD.diagnosis::text, NEW.diagnosis::text, current_setting('app.changed_by', true));
    END IF;
    IF NEW.severity IS DISTINCT FROM OLD.severity THEN
        INSERT INTO case_audit_logs (id, case_id, changed_field, old_value, new_value, changed_by)
        VALUES (gen_random_uuid(), NEW.id, 'severity', OLD.severity::text, NEW.severity::text, current_setting('app.changed_by', true));
    END IF;
    IF NEW.is_confirmed IS DISTINCT FROM OLD.is_confirmed THEN
        INSERT INTO case_audit_logs (id, case_id, changed_field, old_value, new_value, changed_by)
        VALUES (gen_random_uuid(), NEW.id, 'is_confirmed', OLD.is_confirmed::text, NEW.is_confirmed::text, current_setting('app.changed_by', true));
    END IF;
    IF NEW.reported_at IS DISTINCT FROM OLD.reported_at THEN
        INSERT INTO case_audit_logs (id, case_id, changed_field, old_value, new_value, changed_by)
        VALUES (gen_random_uuid(), NEW.id, 'reported_at', OLD.reported_at::text, NEW.reported_at::text, current_setting('app.changed_by', true));
    END IF;
    IF NEW.location IS DISTINCT FROM OLD.location THEN
        INSERT INTO case_audit_logs (id, case_id, changed_field, old_value, new_value, changed_by)
        VALUES (gen_random_uuid(), NEW.id, 'location', ST_AsText(OLD.location), ST_AsText(NEW.location), current_setting('app.changed_by', true));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_case_update ON cases;
CREATE TRIGGER trg_case_update AFTER UPDATE ON cases
    FOR EACH ROW EXECUTE FUNCTION log_case_update();
