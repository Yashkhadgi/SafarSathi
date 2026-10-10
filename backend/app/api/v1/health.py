"""Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text
from backend.app.db.session import SessionLocal

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """System and database connectivity health check."""
    db_status = "healthy"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as exc:
        db_status = f"degraded: {exc}"

    return {
        "status": "ok",
        "service": "safarsathi-api",
        "version": "2.0.0",
        "database": db_status,
    }
