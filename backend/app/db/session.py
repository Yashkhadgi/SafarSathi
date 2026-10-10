"""SQLAlchemy 2 database engine and session factory."""

import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from backend.app.db.base import Base

# Default to SQLite local file in memory/ if DATABASE_URL is not configured
_DEFAULT_DB_FILE = Path(__file__).resolve().parents[3] / "memory" / "safarsathi_v2.db"
_DEFAULT_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
_DEFAULT_SQLITE_URL = f"sqlite:///{_DEFAULT_DB_FILE}"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip() or _DEFAULT_SQLITE_URL

# Normalize postgresql:// to postgresql+psycopg2:// or sqlite compatibility
_engine_url = DATABASE_URL
if _engine_url.startswith("postgres://"):
    _engine_url = _engine_url.replace("postgres://", "postgresql://", 1)

# Connection arguments
connect_args = {}
if _engine_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    _engine_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

# Enable foreign keys for SQLite
if _engine_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting DB session in FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined on Base."""
    # Import all models to register with Base.metadata
    from backend.app.db.models import user, conversation, trip, profile, contact, feedback  # noqa: F401
    Base.metadata.create_all(bind=engine)
