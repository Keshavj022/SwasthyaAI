"""Appointment CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database import get_db
from models.appointment import Appointment

router = APIRouter(prefix="/appointments", tags=["appointments"])


class AppointmentCreate(BaseModel):
    patientId: str
    doctorId: str
    doctorName: Optional[str] = None
    specialty: Optional[str] = None
    dateTime: datetime
    type: str = "consultation"
    notes: Optional[str] = None


class ReschedulePayload(BaseModel):
    dateTime: Optional[datetime] = None
    status: Optional[Literal["scheduled", "confirmed", "pending", "completed", "cancelled"]] = None


def _serialize(a: Appointment) -> dict:
    return {
        "id": a.id,
        "patientId": a.patient_id,
        "doctorId": a.doctor_id,
        "doctorName": a.doctor_name,
        "specialty": a.specialty,
        "dateTime": a.date_time.isoformat() if a.date_time else None,
        "status": a.status,
        "type": a.type,
        "notes": a.notes,
    }


@router.get("/availability")
async def get_availability(
    specialty: Optional[str] = Query(None),
    doctor_name: Optional[str] = Query(None),
):
    """Returns empty availability list (stub — real scheduling in later tasks)."""
    return []


@router.get("")
async def list_appointments(
    patient_id: Optional[str] = Query(None),
    doctor_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Appointment)
    if patient_id:
        q = q.filter(Appointment.patient_id == patient_id)
    if doctor_id:
        q = q.filter(Appointment.doctor_id == doctor_id)
    rows = q.order_by(Appointment.date_time.asc()).all()
    return [_serialize(r) for r in rows]


@router.post("", status_code=201)
async def book_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    appt = Appointment(
        patient_id=payload.patientId,
        doctor_id=payload.doctorId,
        doctor_name=payload.doctorName,
        specialty=payload.specialty,
        date_time=payload.dateTime,
        type=payload.type,
        notes=payload.notes,
        status="scheduled",
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return _serialize(appt)


@router.patch("/{appointment_id}")
async def reschedule_appointment(
    appointment_id: str, payload: ReschedulePayload, db: Session = Depends(get_db)
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if payload.dateTime is not None:
        appt.date_time = payload.dateTime
    if payload.status is not None:
        appt.status = payload.status
    db.commit()
    db.refresh(appt)
    return _serialize(appt)


@router.delete("/{appointment_id}")
async def cancel_appointment(appointment_id: str, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = "cancelled"
    db.commit()
    return {"success": True}
