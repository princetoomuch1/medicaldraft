import uuid
from enum import Enum

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

try:
    from .database import Base
except ImportError:
    from database import Base


class SeverityEnum(str, Enum):
    critical = "critical"
    high = "high"
    moderate = "moderate"
    low = "low"


class AlertLevelEnum(str, Enum):
    red = "red"
    orange = "orange"
    yellow = "yellow"


class UserRoleEnum(str, Enum):
    viewer = "viewer"
    staff = "staff"
    admin = "admin"


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    cases = relationship("Case", back_populates="hospital")
    users = relationship("User", back_populates="hospital")


class User(Base):
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRoleEnum), nullable=False, server_default=UserRoleEnum.viewer.value)
    hospital_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    hospital = relationship("Hospital", back_populates="users")


class Case(Base):
    __tablename__ = "cases"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reported_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    diagnosis = Column(String(255), nullable=False)
    severity = Column(SAEnum(SeverityEnum), nullable=False)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    is_confirmed = Column(Boolean, nullable=False, default=True)

    hospital = relationship("Hospital", back_populates="cases")

    __table_args__ = (
        Index("idx_cases_severity_reported_at", "severity", text("reported_at DESC")),
    )


class AlertZone(Base):
    __tablename__ = "alert_zones"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_name = Column(String(255), nullable=False)
    alert_level = Column(SAEnum(AlertLevelEnum), nullable=False)
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CaseAuditLog(Base):
    __tablename__ = "case_audit_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    case_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    changed_field = Column(String(255), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    changed_by = Column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_case_audit_logs_changed_at", "changed_at"),
    )
