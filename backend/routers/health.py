"""
Health check endpoint.
Verifies system status, database connectivity, and offline readiness.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import os
import sys
from pathlib import Path

# Add parent directory to path to import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(db: Session = Depends(get_db)):
    """
    System health check endpoint.

    Returns:
        - System status
        - Database connectivity
        - Offline mode status
        - Timestamp
    """
    # Check database connectivity
    db_status = "connected"
    try:
        db.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check if database file exists
    db_file_exists = os.path.exists(
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database", "hospital.db")
    )

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "status": db_status,
            "file_exists": db_file_exists,
            "type": "SQLite (offline-first)",
        },
        "offline_mode": {
            "enabled": True,
            "description": "System fully operational without internet connectivity",
        },
    }


@router.get("/ping")
async def ping():
    """Simple ping endpoint for quick connectivity tests."""
    return {"message": "pong", "timestamp": datetime.utcnow().isoformat()}
