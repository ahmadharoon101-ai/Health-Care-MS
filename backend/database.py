"""
SQLAlchemy engine/session setup.

A single SQLite file (backend/data/app.db) is used by default so the whole
system still runs with zero external services, matching the "existing
database configuration" philosophy of this project (previously the medicine
catalog was the only "data store", loaded from CSV). Set DATABASE_URL in
.env to point at Postgres/MySQL/etc. in production — the rest of the code
only talks to SQLAlchemy, so no other changes are needed.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend import config

connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(config.DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables that don't exist yet. Safe to call on every startup."""
    # Import models here so they're registered on Base.metadata before create_all.
    from backend import models_db  # noqa: F401

    Base.metadata.create_all(bind=engine)
