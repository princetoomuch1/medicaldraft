import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/medicaldraft",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

__all__ = ["engine", "SessionLocal", "Base", "get_db", "DATABASE_URL"]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
