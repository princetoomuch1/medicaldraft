import uuid

from geoalchemy2 import WKTElement

try:
    from .database import SessionLocal
    from .models import AlertZone, Case, Hospital, AlertLevelEnum, SeverityEnum
except ImportError:
    from database import SessionLocal
    from models import AlertZone, Case, Hospital, AlertLevelEnum, SeverityEnum

def seed():
    db = SessionLocal()
    try:
        if db.query(Hospital).count() == 0:
            hospitals = [
                Hospital(
                    id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    name="Bangalore Medical Center",
                    latitude=12.9716,
                    longitude=77.5946,
                ),
                Hospital(
                    id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                    name="Hyderabad Health Institute",
                    latitude=17.3850,
                    longitude=78.4867,
                ),
            ]
            db.add_all(hospitals)
            db.flush()

        if db.query(Case).count() == 0:
            sample_cases = [
                Case(
                    id=uuid.uuid4(),
                    hospital_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    diagnosis="Influenza outbreak",
                    severity=SeverityEnum.critical,
                    location=WKTElement("POINT(77.5946 12.9716)", srid=4326),
                    is_confirmed=True,
                ),
                Case(
                    id=uuid.uuid4(),
                    hospital_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                    diagnosis="Respiratory infection cluster",
                    severity=SeverityEnum.moderate,
                    location=WKTElement("POINT(78.4867 17.3850)", srid=4326),
                    is_confirmed=True,
                ),
            ]
            db.add_all(sample_cases)

        if db.query(AlertZone).count() == 0:
            sample_alerts = [
                AlertZone(
                    id=uuid.uuid4(),
                    zone_name="Central Ward",
                    alert_level=AlertLevelEnum.red,
                    geometry=WKTElement("POLYGON((76.5 12.5, 78.5 12.5, 78.5 13.5, 76.5 13.5, 76.5 12.5))", srid=4326),
                )
            ]
            db.add_all(sample_alerts)

        db.commit()
        print("Seed data inserted")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
