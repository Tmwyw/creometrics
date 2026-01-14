"""Database connection and session management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config.settings import settings

# Debug: Print DATABASE_URL to see what we're getting
print(f"[DEBUG] DATABASE_URL from env: {os.getenv('DATABASE_URL', 'NOT_SET')[:50]}...")
print(f"[DEBUG] DATABASE_URL from settings: {settings.DATABASE_URL[:50] if settings.DATABASE_URL else 'EMPTY'}...")
print(f"[DEBUG] RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', 'NOT_SET')}")

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Get database session.

    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    from database.models import Base
    Base.metadata.create_all(bind=engine)
