"""
Admin management API (Task 10).

Mounted under ``require_admin`` in main.py, so EVERY route here is admin-only.
Provides user listing/management and a system-wide statistics summary.

Soft-delete semantics: DELETE deactivates the user (is_active=False) rather than
removing the row, preserving audit/appointment references. Guards prevent an
admin from deleting themselves or removing the last remaining active admin.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Literal
from datetime import datetime, date
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database import get_db
from models.user import User
from models.system import AuditLog
from models.appointment import Appointment
from models.patient import Patient, DocumentAttachment
from services.auth_service import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AdminUserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    isActive: bool
    createdAt: datetime


class UserUpdate(BaseModel):
    role: Optional[Literal["doctor", "patient", "admin"]] = None
    isActive: Optional[bool] = None


def _serialize_user(u: User) -> AdminUserOut:
    return AdminUserOut(
        id=u.id,
        name=u.full_name,
        email=u.email,
        role=u.role,
        isActive=u.is_active,
        createdAt=u.created_at,
    )


def _active_admin_count(db: Session, exclude_id: Optional[str] = None) -> int:
    q = db.query(User).filter(User.role == "admin", User.is_active == True)  # noqa: E712
    if exclude_id:
        q = q.filter(User.id != exclude_id)
    return q.count()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@router.get("/users", response_model=list[AdminUserOut])
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    q: Optional[str] = Query(None, description="Search name or email"),
    db: Session = Depends(get_db),
):
    """List users, optionally filtered by role and a name/email search term."""
    query = db.query(User)
    if role and role.lower() != "all":
        query = query.filter(User.role == role)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            (User.full_name.ilike(term)) | (User.email.ilike(term))
        )
    users = query.order_by(User.created_at.desc()).all()
    return [_serialize_user(u) for u in users]


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a user's role and/or active status."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Guard: do not allow demoting / deactivating the last active admin.
    demoting_admin = (
        user.role == "admin"
        and (
            (payload.role is not None and payload.role != "admin")
            or (payload.isActive is False)
        )
    )
    if demoting_admin and _active_admin_count(db, exclude_id=user.id) == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot demote or deactivate the last remaining admin",
        )

    # Guard: an admin cannot deactivate their own account (would lock them out).
    if payload.isActive is False and str(user.id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")

    if payload.role is not None:
        user.role = payload.role
    if payload.isActive is not None:
        user.is_active = payload.isActive

    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a user (deactivate). Blocks self-delete and last-admin delete."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    if user.role == "admin" and _active_admin_count(db, exclude_id=user.id) == 0:
        raise HTTPException(
            status_code=400, detail="Cannot delete the last remaining admin"
        )

    # Soft delete — preserve referential history (audit, appointments).
    user.is_active = False
    db.commit()
    return {"success": True}


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """System-wide counts for the admin dashboard."""
    total_users = db.query(User).count()
    total_doctors = db.query(User).filter(User.role == "doctor").count()
    total_patients = db.query(Patient).count()
    total_appointments = db.query(Appointment).count()
    total_documents = db.query(DocumentAttachment).count()
    total_audit_logs = db.query(AuditLog).count()

    start_of_today = datetime.combine(date.today(), datetime.min.time())
    ai_queries_today = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "agent_query",
            AuditLog.timestamp >= start_of_today,
        )
        .count()
    )

    return {
        "totalUsers": total_users,
        "totalPatients": total_patients,
        "totalDoctors": total_doctors,
        "totalAppointments": total_appointments,
        "totalDocuments": total_documents,
        "totalAuditLogs": total_audit_logs,
        "aiQueriesToday": ai_queries_today,
    }
