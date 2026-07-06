from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CaseCreate(BaseModel):
    hospital_id: Optional[UUID] = None
    diagnosis: str = Field(..., min_length=1, max_length=500)
    severity: Literal["critical", "high", "moderate", "low"]
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    is_confirmed: bool = True


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hospital_id: Optional[UUID] = None
    reported_at: datetime
    diagnosis: str
    severity: str
    latitude: float
    longitude: float
    is_confirmed: bool


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    zone_name: str
    alert_level: str
    issued_at: datetime


class HospitalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"]
    expires_at: datetime


class TokenRefresh(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: str
    hospital_id: Optional[UUID] = None
