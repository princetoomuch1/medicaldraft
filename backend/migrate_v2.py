"""One-time migration script for Medical Draft backend data layer v2.

=============================================================================
  !!!  DANGER  --  READ BEFORE RUNNING  !!!
=============================================================================
  This script DROPS and RECREATES all core tables (hospitals, cases,
  alert_zones, case_audit_logs) and the enum types. Running it with
  `--execute` is DESTRUCTIVE.

  NEVER run `--execute` against a production database without a TESTED,
  VERIFIED backup that you have confirmed you can restore. The built-in
  JSON backup is a convenience, not a substitute for a real DB backup.
=============================================================================

Usage:
    python migrate_v2.py --backup-only [--backup-file PATH]
    python migrate_v2.py --execute [--backup-file PATH]
    python migrate_v2.py --rollback backup_file.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from geoalchemy2 import WKTElement
from sqlalchemy import create_engine, text

try:
    from .database import Base
    from .models import AlertZone, Case  # noqa: F401  (ensures models registered)
    from . import models  # noqa: F401
except ImportError:
    from database import Base
    from models import AlertZone, Case  # noqa: F401
    import models  # noqa: F401


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/medicaldraft",
)


TRIGGER_DDL = """
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
"""


def backup_data(engine, path: str) -> dict:
    """Dump hospitals, cases, and alert_zones to a JSON file (geometry as WKT)."""
    with engine.connect() as conn:
        hospitals = [
            dict(row._mapping)
            for row in conn.execute(
                text(
                    """
                    SELECT id, name, latitude, longitude, created_at
                    FROM hospitals
                    """
                )
            )
        ]
        cases = [
            dict(row._mapping)
            for row in conn.execute(
                text(
                    """
                    SELECT id, hospital_id, reported_at, diagnosis, severity,
                           ST_AsText(location) AS location_wkt, is_confirmed
                    FROM cases
                    """
                )
            )
        ]
        users = [
            dict(row._mapping)
            for row in conn.execute(
                text(
                    """
                    SELECT id, email, password_hash, role, hospital_id, created_at, updated_at
                    FROM users
                    """
                )
            )
        ]
        alert_zones = [
            dict(row._mapping)
            for row in conn.execute(
                text(
                    """
                    SELECT id, zone_name, alert_level,
                           ST_AsText(geometry) AS geometry_wkt, issued_at
                    FROM alert_zones
                    """
                )
            )
        ]

    backup = {"hospitals": hospitals, "cases": cases, "users": users, "alert_zones": alert_zones}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(backup, fh, default=str, indent=2)

    print(
        f"Backup written to {path}: {len(hospitals)} hospitals, {len(cases)} cases, {len(users)} users, {len(alert_zones)} alert_zones"
    )
    return backup


def migrate_schema(engine) -> None:
    """Drop old objects, recreate tables via ORM metadata, install trigger."""
    with engine.connect() as conn:
        conn.execute(
            text("DROP TABLE IF EXISTS case_audit_logs, cases, alert_zones, users, hospitals CASCADE;")
        )
        conn.execute(text("DROP TYPE IF EXISTS severity_enum, alert_level_enum, userroleenum CASCADE;"))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text(TRIGGER_DDL))
        conn.commit()

    print("Schema recreated and audit trigger installed")


def restore_data(engine, backup: dict) -> None:
    """Reinsert hospitals, cases, and alert_zones."""
    hospitals = backup.get("hospitals", [])
    cases = backup.get("cases", [])
    alert_zones = backup.get("alert_zones", [])

    with engine.connect() as conn:
        for row in hospitals:
            conn.execute(
                text(
                    """
                    INSERT INTO hospitals (id, name, latitude, longitude, created_at)
                    VALUES (:id, :name, :latitude, :longitude, :created_at)
                    ON CONFLICT (id) DO NOTHING
                    """
                ),
                {
                    "id": row["id"],
                    "name": row["name"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "created_at": row["created_at"],
                },
            )

        existing_hospital_ids = {
            row[0]
            for row in conn.execute(text("SELECT id FROM hospitals"))
        }

        for row in cases:
            hospital_id = row["hospital_id"] if row["hospital_id"] in existing_hospital_ids else None
            conn.execute(
                text(
                    """
                    INSERT INTO cases (id, hospital_id, reported_at, diagnosis,
                                       severity, location, is_confirmed)
                    VALUES (:id, :hospital_id, :reported_at, :diagnosis, :severity,
                            ST_GeomFromText(:location_wkt, 4326), :is_confirmed)
                    """
                ),
                {
                    "id": row["id"],
                    "hospital_id": hospital_id,
                    "reported_at": row["reported_at"],
                    "diagnosis": row["diagnosis"],
                    "severity": row["severity"],
                    "location_wkt": row["location_wkt"],
                    "is_confirmed": row["is_confirmed"],
                },
            )

        for row in users:
            hospital_id = row["hospital_id"] if row["hospital_id"] in existing_hospital_ids else None
            conn.execute(
                text(
                    """
                    INSERT INTO users (id, email, password_hash, role, hospital_id, created_at, updated_at)
                    VALUES (:id, :email, :password_hash, :role, :hospital_id, :created_at, :updated_at)
                    ON CONFLICT (id) DO NOTHING
                    """
                ),
                {
                    "id": row["id"],
                    "email": row["email"],
                    "password_hash": row["password_hash"],
                    "role": row["role"],
                    "hospital_id": hospital_id,
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                },
            )

        for row in alert_zones:
            conn.execute(
                text(
                    """
                    INSERT INTO alert_zones (id, zone_name, alert_level, geometry, issued_at)
                    VALUES (:id, :zone_name, :alert_level,
                            ST_GeomFromText(:geometry_wkt, 4326), :issued_at)
                    """
                ),
                {
                    "id": row["id"],
                    "zone_name": row["zone_name"],
                    "alert_level": row["alert_level"],
                    "geometry_wkt": row["geometry_wkt"],
                    "issued_at": row["issued_at"],
                },
            )
        conn.commit()

    print(
        f"Restored {len(hospitals)} hospitals, {len(cases)} cases, {len(users)} users, and {len(alert_zones)} alert_zones"
    )


def _default_backup_file() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"backup_{stamp}.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Medical Draft v2 data-layer migration")
    parser.add_argument("--backup-only", action="store_true", help="Only dump data to JSON")
    parser.add_argument("--execute", action="store_true", help="Backup, drop/recreate, restore")
    parser.add_argument("--rollback", metavar="FILE", help="Restore data from a backup JSON file")
    parser.add_argument("--backup-file", default=_default_backup_file(), help="Backup file path")
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    if args.rollback:
        with open(args.rollback, "r", encoding="utf-8") as fh:
            backup = json.load(fh)
        restore_data(engine, backup)
        return 0

    if args.backup_only:
        backup_data(engine, args.backup_file)
        return 0

    if args.execute:
        answer = input("This will DROP and recreate all tables. Continue? (yes/no) ").strip().lower()
        if answer != "yes":
            print("Aborted.")
            return 1
        backup = backup_data(engine, args.backup_file)
        migrate_schema(engine)
        restore_data(engine, backup)
        print("Migration complete.")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
