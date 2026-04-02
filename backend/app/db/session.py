from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os

from app.core.config import settings


def get_database_url() -> str:
    url = settings.DATABASE_URL or os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


database_url = get_database_url()
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
