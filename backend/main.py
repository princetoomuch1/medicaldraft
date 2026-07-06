import json
import logging
import math
import os
import uuid
from datetime import datetime, timedelta
from typing import Annotated

import jwt
import redis
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from geoalchemy2 import WKTElement
from passlib.context import CryptContext
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

try:
    from .database import SessionLocal, get_db
    from .models import AlertZone, Case, Hospital, SeverityEnum, User, UserRoleEnum
    from .schemas import AlertResponse, CaseCreate, CaseResponse, TokenRefresh, TokenResponse, UserLogin, UserResponse
except ImportError:
    from database import SessionLocal, get_db
    from models import AlertZone, Case, Hospital, SeverityEnum, User, UserRoleEnum
    from schemas import AlertResponse, CaseCreate, CaseResponse, TokenRefresh, TokenResponse, UserLogin, UserResponse

logger = logging.getLogger("medical_draft")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
)

app = FastAPI(title="Medical Draft API")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
allow_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
API_KEY = os.getenv("API_KEY")
GRID_DEGREES = 1.0
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "medicaldraft-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

in_memory_cases: list[dict] = []
in_memory_alerts: list[dict] = []


def check_db_health(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as exc:
        logger.warning("Database health check failed: %s", exc)
        return False


def require_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")):
    if API_KEY is None:
        return
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_token(subject: str, role: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("type") != expected_type:
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials if credentials else None
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    payload = decode_token(token, expected_type="access")
    user = get_user_by_id(db, payload.get("sub"))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_role(allowed_roles: list[UserRoleEnum]):
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return role_checker


def _serialize_case(item: Case | dict) -> dict:
    if isinstance(item, dict):
        return item
    return {
        "id": str(item.id),
        "hospital_id": str(item.hospital_id) if item.hospital_id else None,
        "reported_at": item.reported_at.isoformat() if item.reported_at else None,
        "diagnosis": item.diagnosis,
        "severity": item.severity.value if hasattr(item.severity, "value") else str(item.severity),
        "latitude": float(item.location.y) if item.location else None,
        "longitude": float(item.location.x) if item.location else None,
        "is_confirmed": item.is_confirmed,
    }


def _filter_cases_in_memory(bbox: tuple[float, float, float, float]) -> list[dict]:
    west, south, east, north = bbox
    return [
        item
        for item in in_memory_cases
        if west <= item["longitude"] <= east and south <= item["latitude"] <= north
    ]


def _validate_bbox(bbox: str) -> tuple[float, float, float, float]:
    parts = bbox.split(",")
    if len(parts) != 4:
        raise HTTPException(status_code=400, detail="bbox must have exactly 4 comma-separated values")
    try:
        west, south, east, north = (float(value) for value in parts)
    except ValueError:
        raise HTTPException(status_code=400, detail="bbox values must be numeric")
    if not (-180 <= west <= 180 and -180 <= east <= 180):
        raise HTTPException(status_code=400, detail="longitude out of range")
    if not (-90 <= south <= 90 and -90 <= north <= 90):
        raise HTTPException(status_code=400, detail="latitude out of range")
    if west > east or south > north:
        raise HTTPException(status_code=400, detail="bbox bounds are invalid")
    return west, south, east, north


def _cache_key_for_bbox(west: float, south: float, east: float, north: float, limit: int, offset: int) -> str:
    return f"cases:{west}:{south}:{east}:{north}:{limit}:{offset}"


def _bbox_index_keys(west: float, south: float, east: float, north: float) -> list[str]:
    lat_start = int(math.floor(south / GRID_DEGREES))
    lat_end = int(math.floor(north / GRID_DEGREES))
    lng_start = int(math.floor(west / GRID_DEGREES))
    lng_end = int(math.floor(east / GRID_DEGREES))
    keys = []
    for lat in range(lat_start, lat_end + 1):
        for lng in range(lng_start, lng_end + 1):
            keys.append(f"cases:index:{lat}:{lng}")
    return keys


def _location_index_key(latitude: float, longitude: float) -> str:
    lat_bucket = int(math.floor(latitude / GRID_DEGREES))
    lng_bucket = int(math.floor(longitude / GRID_DEGREES))
    return f"cases:index:{lat_bucket}:{lng_bucket}"


def _register_cache_key(cache_key: str, west: float, south: float, east: float, north: float) -> None:
    index_keys = _bbox_index_keys(west, south, east, north)
    try:
        for index_key in index_keys:
            redis_client.sadd(index_key, cache_key)
    except RedisError as exc:
        logger.warning("Failed to register cache key '%s': %s", cache_key, exc)


def _invalidate_cache_for_location(latitude: float, longitude: float) -> None:
    index_key = _location_index_key(latitude, longitude)
    try:
        cache_keys = redis_client.smembers(index_key)
        if cache_keys:
            redis_client.delete(*cache_keys)
        redis_client.delete(index_key)
    except RedisError as exc:
        logger.warning(
            "Redis cache invalidation failed for lat=%s lng=%s: %s",
            latitude,
            longitude,
            exc,
        )


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_token(str(user.id), user.role.value, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")
    refresh_token = create_token(str(user.id), user.role.value, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


@app.post("/api/auth/refresh", response_model=TokenResponse)
def refresh_token(payload: TokenRefresh, db: Session = Depends(get_db)):
    token_data = decode_token(payload.refresh_token, expected_type="refresh")
    user = get_user_by_id(db, token_data.get("sub"))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_token(str(user.id), user.role.value, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")
    refresh_token = create_token(str(user.id), user.role.value, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


@app.get("/api/users/me", response_model=UserResponse)
def current_user(user: User = Depends(get_current_user)):
    return user


@app.post("/api/cases", response_model=CaseResponse, dependencies=[Depends(require_api_key)])
def create_case(payload: CaseCreate):
    db = SessionLocal()
    try:
        if check_db_health(db):
            try:
                with db.begin():
                    if payload.hospital_id is not None:
                        hospital = db.get(Hospital, payload.hospital_id)
                        if hospital is None:
                            raise HTTPException(status_code=400, detail="Hospital not found")
                    point = WKTElement(
                        f"POINT({payload.longitude} {payload.latitude})",
                        srid=4326,
                    )
                    case = Case(
                        id=uuid.uuid4(),
                        hospital_id=payload.hospital_id,
                        diagnosis=payload.diagnosis,
                        severity=SeverityEnum(payload.severity),
                        location=point,
                        is_confirmed=payload.is_confirmed,
                    )
                    db.add(case)
            except HTTPException:
                raise
            except SQLAlchemyError as exc:
                logger.error(
                    "create_case failed for hospital_id=%s severity=%s: %s",
                    payload.hospital_id,
                    payload.severity,
                    exc,
                )
                raise HTTPException(status_code=500, detail="Database error")
            db.refresh(case)
        else:
            case = {
                "id": str(uuid.uuid4()),
                "hospital_id": str(payload.hospital_id) if payload.hospital_id else None,
                "reported_at": datetime.utcnow().isoformat(),
                "diagnosis": payload.diagnosis,
                "severity": payload.severity,
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "is_confirmed": payload.is_confirmed,
            }
            in_memory_cases.append(case)
            return CaseResponse(**case)
    finally:
        db.close()

    _invalidate_cache_for_location(payload.latitude, payload.longitude)

    return CaseResponse(
        id=case.id,
        hospital_id=case.hospital_id,
        reported_at=case.reported_at,
        diagnosis=case.diagnosis,
        severity=case.severity.value,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_confirmed=case.is_confirmed,
    )


@app.get("/api/cases")
def get_cases(
    bbox: str = Query(...),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    west, south, east, north = _validate_bbox(bbox)
    cache_key = _cache_key_for_bbox(west, south, east, north, limit, offset)

    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except RedisError as exc:
        logger.warning("Redis read failed for cache key %s: %s", cache_key, exc)

    if not check_db_health(db):
        rows = _filter_cases_in_memory((west, south, east, north))
        return {
            "total_count": len(rows),
            "items": rows[offset : offset + limit],
        }

    try:
        count_query = text(
            "SELECT COUNT(*) FROM cases "
            "WHERE ST_Within(location, ST_MakeEnvelope(:west, :south, :east, :north, 4326))"
        )
        total_count = db.execute(
            count_query,
            {
                "west": west,
                "south": south,
                "east": east,
                "north": north,
            },
        ).scalar_one()

        query = text(
            """
            SELECT id, hospital_id, reported_at, diagnosis, severity,
                   ST_Y(location::geometry) AS latitude,
                   ST_X(location::geometry) AS longitude,
                   is_confirmed
            FROM cases
            WHERE ST_Within(location, ST_MakeEnvelope(:west, :south, :east, :north, 4326))
            ORDER BY reported_at DESC
            LIMIT :limit OFFSET :offset
            """
        )
        result = db.execute(
            query,
            {
                "west": west,
                "south": south,
                "east": east,
                "north": north,
                "limit": limit,
                "offset": offset,
            },
        )
        rows = [
            {
                "id": str(row[0]),
                "hospital_id": str(row[1]) if row[1] else None,
                "reported_at": row[2].isoformat() if row[2] else None,
                "diagnosis": row[3],
                "severity": row[4],
                "latitude": row[5],
                "longitude": row[6],
                "is_confirmed": row[7],
            }
            for row in result.fetchall()
        ]
    except SQLAlchemyError as exc:
        logger.error(
            "GET /api/cases failed for bbox=%s limit=%s offset=%s: %s",
            bbox,
            limit,
            offset,
            exc,
        )
        rows = _filter_cases_in_memory((west, south, east, north))
        return {"total_count": len(rows), "items": rows[offset : offset + limit]}

    payload = {"total_count": total_count, "items": rows}
    try:
        redis_client.setex(cache_key, 300, json.dumps(payload))
        _register_cache_key(cache_key, west, south, east, north)
    except RedisError as exc:
        logger.warning("Redis write failed for cache key %s: %s", cache_key, exc)
    return payload


@app.get("/api/alerts", response_model=list[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    if not check_db_health(db):
        logger.warning("GET /api/alerts using in-memory fallback because DB is unavailable")
        return [AlertResponse(**item) for item in in_memory_alerts]

    try:
        alerts = db.query(AlertZone).all()
        return [
            AlertResponse(
                id=alert.id,
                zone_name=alert.zone_name,
                alert_level=alert.alert_level.value,
                issued_at=alert.issued_at,
            )
            for alert in alerts
        ]
    except SQLAlchemyError as exc:
        logger.warning("GET /api/alerts failed: %s", exc)
        return [AlertResponse(**item) for item in in_memory_alerts]


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    healthy = check_db_health(db)
    return {"status": "ok" if healthy else "degraded"}
