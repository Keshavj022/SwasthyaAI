"""
Admin API — user management, system stats, and all-appointments view.
All routes require admin role (enforced in main.py via Depends(require_admin)).
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models.user import User
from models.system import AuditLog
from models.patient import Patient, DocumentAttachment
from models.appointment import Appointment
from services.auth_service import hash_password, require_admin, get_current_user

VALID_ROLES = frozenset(("doctor", "patient", "admin"))

router = APIRouter(prefix="/admin", tags=["admin"])


class UserPublic(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str


class PasswordResetResponse(BaseModel):
    temp_password: str


class AdminStats(BaseModel):
    db_size_kb: float
    total_patients: int
    total_audit_logs: int
    total_documents: int
    agent_requests: List[dict]


@router.get("/users", response_model=List[UserPublic])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        UserPublic(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name or "",
            role=u.role or "patient",
            is_active=bool(u.is_active),
            created_at=u.created_at.isoformat() if u.created_at else None,
        )
        for u in users
    ]


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserPublic)
def create_user(body: UserCreateRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail="Invalid role")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserPublic(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name or "",
        role=user.role,
        is_active=True,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.patch("/users/{user_id}", response_model=UserPublic)
def update_user(user_id: str, body: UserUpdateRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role is not None:
        if body.role not in VALID_ROLES:
            raise HTTPException(status_code=422, detail="Invalid role")
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return UserPublic(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name or "",
        role=user.role,
        is_active=bool(user.is_active),
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.post("/users/{user_id}/reset-password", response_model=PasswordResetResponse)
def reset_password(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    alphabet = string.ascii_letters + string.digits
    temp_password = "Temp" + "".join(secrets.choice(alphabet) for _ in range(8)) + "!"
    user.hashed_password = hash_password(temp_password)
    db.commit()
    return PasswordResetResponse(temp_password=temp_password)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if str(current_user.id) == str(user_id):
        raise HTTPException(status_code=409, detail="Cannot delete your own account")
    if user.is_active:
        raise HTTPException(status_code=409, detail="Deactivate the user before deleting")
    db.delete(user)
    db.commit()


@router.get("/stats", response_model=AdminStats)
def get_stats(db: Session = Depends(get_db)):
    db_path = Path(__file__).parent.parent / "swasthya.db"
    db_size_kb = round(db_path.stat().st_size / 1024, 1) if db_path.exists() else 0.0
    total_patients = db.query(func.count(Patient.id)).scalar() or 0
    total_audit_logs = db.query(func.count(AuditLog.id)).scalar() or 0
    total_documents = db.query(func.count(DocumentAttachment.id)).scalar() or 0
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    rows = (
        db.query(AuditLog.agent_name, func.count(AuditLog.id).label("count"))
        .filter(AuditLog.timestamp >= seven_days_ago)
        .group_by(AuditLog.agent_name)
        .all()
    )
    agent_requests = [{"agent_name": r.agent_name or "unknown", "count": r.count} for r in rows]
    return AdminStats(
        db_size_kb=db_size_kb,
        total_patients=total_patients,
        total_audit_logs=total_audit_logs,
        total_documents=total_documents,
        agent_requests=agent_requests,
    )


@router.get("/appointments")
def list_all_appointments(
    status_filter: Optional[str] = Query(None, alias="status"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Appointment)
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    if specialty:
        query = query.filter(Appointment.specialty == specialty)
    if from_date:
        try:
            query = query.filter(Appointment.date_time >= datetime.fromisoformat(from_date))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid from_date format, expected ISO 8601 (YYYY-MM-DD)")
    if to_date:
        try:
            query = query.filter(Appointment.date_time <= datetime.fromisoformat(to_date))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid to_date format, expected ISO 8601 (YYYY-MM-DD)")
    total = query.count()
    appts = query.order_by(Appointment.date_time.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "appointments": [
            {
                "id": str(a.id),
                "patient_id": str(a.patient_id),
                "doctor_id": str(a.doctor_id) if a.doctor_id else None,
                "doctor_name": a.doctor_name,
                "specialty": a.specialty if hasattr(a, "specialty") else None,
                "date_time": a.date_time.isoformat() if isinstance(a.date_time, datetime) else str(a.date_time),
                "status": a.status,
                "type": a.type if hasattr(a, "type") else None,
                "notes": a.notes,
            }
            for a in appts
        ],
    }
