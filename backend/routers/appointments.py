"""Appointment endpoints — DB-backed scheduling with conflict detection.

All persistence goes through the SQLAlchemy ``Appointment`` table. The booking
flow validates the requested doctor, rejects past dates and double-bookings on
``(doctor_id, date_time)`` (with overlap awareness via duration), and returns the
next available slots when a slot is taken.

The :class:`Scheduler` defined here is the single source of scheduling truth. The
appointment agent (``agents/appointment_agent.py``) imports it so its conflict
detection operates on the same persisted data.

Object-level authorization:
- Patients see/modify only appointments where they are the patient.
- Doctors see/modify only appointments where they are the doctor.
- Admins may act on any appointment.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database import get_db
from models.appointment import Appointment
from models.user import User
from services.auth_service import get_current_user

router = APIRouter(prefix="/appointments", tags=["appointments"])

# Scheduling constants
SLOT_MINUTES = 30
DEFAULT_DURATION = 30
MAX_LOOKAHEAD_DAYS = 30

# Clinic operating hours (24h). None = closed.
CLINIC_HOURS = {
    0: ("08:00", "18:00"),  # Monday
    1: ("08:00", "18:00"),
    2: ("08:00", "18:00"),
    3: ("08:00", "18:00"),
    4: ("08:00", "17:00"),  # Friday
    5: ("09:00", "13:00"),  # Saturday
    6: None,                # Sunday — closed
}

# Demo doctor roster used when no doctor Users have been seeded yet, so the
# availability + booking flow is exercisable end-to-end during a demo. Real
# doctor Users (role="doctor") always take precedence.
DEMO_DOCTORS = [
    {"id": "doctor_001", "name": "Dr. Sarah Johnson", "specialty": "Family Medicine"},
    {"id": "doctor_002", "name": "Dr. Michael Chen", "specialty": "Cardiology"},
    {"id": "doctor_003", "name": "Dr. Emily Rodriguez", "specialty": "Pediatrics"},
    {"id": "doctor_004", "name": "Dr. James Wilson", "specialty": "Internal Medicine"},
    {"id": "doctor_005", "name": "Dr. Priya Sharma", "specialty": "Cardiology"},
    {"id": "doctor_006", "name": "Dr. Rahul Mehta", "specialty": "Neurology"},
]


# ---------------------------------------------------------------------------
# Scheduler — shared by the router and the appointment agent
# ---------------------------------------------------------------------------

class Scheduler:
    """Stateless scheduling helpers operating directly on the database."""

    def _hhmm(self, value: str) -> tuple:
        h, m = value.split(":")
        return int(h), int(m)

    def is_within_clinic_hours(self, dt: datetime, duration_minutes: int) -> bool:
        hours = CLINIC_HOURS.get(dt.weekday())
        if not hours:
            return False
        open_h, open_m = self._hhmm(hours[0])
        close_h, close_m = self._hhmm(hours[1])
        open_dt = dt.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
        close_dt = dt.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
        end_dt = dt + timedelta(minutes=duration_minutes)
        return open_dt <= dt and end_dt <= close_dt

    def list_doctors(
        self,
        db: Session,
        specialty: Optional[str] = None,
        doctor_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return doctors from the User table, falling back to the demo roster."""
        doctors: List[Dict[str, Any]] = []
        user_docs = (
            db.query(User)
            .filter(User.role == "doctor", User.is_active == True)  # noqa: E712
            .all()
        )
        for u in user_docs:
            doctors.append(
                {"id": str(u.id), "name": u.full_name, "specialty": u.specialty or "General"}
            )
        if not doctors:
            doctors = [dict(d) for d in DEMO_DOCTORS]

        def _match(d: Dict[str, Any]) -> bool:
            if specialty and (d.get("specialty") or "").lower() != specialty.lower():
                return False
            if doctor_name and doctor_name.lower() not in (d.get("name") or "").lower():
                return False
            return True

        return [d for d in doctors if _match(d)]

    def resolve_doctor(
        self,
        db: Session,
        doctor_id: Optional[str] = None,
        doctor_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Resolve a single doctor by id or name; None if not found."""
        if doctor_id:
            user = (
                db.query(User)
                .filter(User.id == doctor_id, User.role == "doctor")
                .first()
            )
            if user:
                return {
                    "id": str(user.id),
                    "name": user.full_name,
                    "specialty": user.specialty or "General",
                }
            for d in DEMO_DOCTORS:
                if d["id"] == doctor_id:
                    return dict(d)
        if doctor_name:
            for d in self.list_doctors(db, doctor_name=doctor_name):
                return d
        return None

    def _booked_intervals(
        self, db: Session, doctor_id: str, day: datetime
    ) -> List[tuple]:
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        rows = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == str(doctor_id),
                Appointment.status != "cancelled",
                Appointment.date_time >= start,
                Appointment.date_time < end,
            )
            .all()
        )
        return [
            (r.date_time, r.date_time + timedelta(minutes=r.duration_minutes or DEFAULT_DURATION))
            for r in rows
        ]

    def has_conflict(
        self,
        db: Session,
        doctor_id: str,
        start: datetime,
        duration_minutes: int,
        exclude_id: Optional[str] = None,
    ) -> bool:
        """True if [start, start+duration) overlaps any non-cancelled booking."""
        end = start + timedelta(minutes=duration_minutes)
        q = db.query(Appointment).filter(
            Appointment.doctor_id == str(doctor_id),
            Appointment.status != "cancelled",
        )
        if exclude_id:
            q = q.filter(Appointment.id != exclude_id)
        for r in q.all():
            r_start = r.date_time
            r_end = r.date_time + timedelta(minutes=r.duration_minutes or DEFAULT_DURATION)
            if start < r_end and end > r_start:
                return True
        return False

    def day_slots(
        self, db: Session, doctor_id: str, day: datetime, duration_minutes: int
    ) -> List[str]:
        """Available start times (ISO) for a doctor on a given day."""
        hours = CLINIC_HOURS.get(day.weekday())
        if not hours:
            return []
        open_h, open_m = self._hhmm(hours[0])
        close_h, close_m = self._hhmm(hours[1])
        cursor = day.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
        close_dt = day.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
        booked = self._booked_intervals(db, doctor_id, day)
        now = datetime.now()

        slots: List[str] = []
        while cursor + timedelta(minutes=duration_minutes) <= close_dt:
            slot_end = cursor + timedelta(minutes=duration_minutes)
            if cursor >= now:
                overlap = any(cursor < b_end and slot_end > b_start for b_start, b_end in booked)
                if not overlap:
                    slots.append(cursor.isoformat())
            cursor += timedelta(minutes=SLOT_MINUTES)
        return slots

    def next_available_slots(
        self,
        db: Session,
        doctor_id: str,
        from_dt: datetime,
        duration_minutes: int,
        count: int = 5,
    ) -> List[str]:
        """Find the next `count` bookable slots at/after `from_dt`."""
        results: List[str] = []
        day = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        for _ in range(MAX_LOOKAHEAD_DAYS):
            for slot in self.day_slots(db, doctor_id, day, duration_minutes):
                if datetime.fromisoformat(slot) >= from_dt:
                    results.append(slot)
                    if len(results) >= count:
                        return results
            day += timedelta(days=1)
        return results

    def get_availability(
        self,
        db: Session,
        specialty: Optional[str] = None,
        doctor_name: Optional[str] = None,
        days: int = 14,
    ) -> List[Dict[str, Any]]:
        """Per-doctor availability list matching the frontend DoctorAvailability."""
        days = min(days, MAX_LOOKAHEAD_DAYS)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        out: List[Dict[str, Any]] = []
        for doc in self.list_doctors(db, specialty=specialty, doctor_name=doctor_name):
            slots: List[str] = []
            for offset in range(days):
                slots.extend(
                    self.day_slots(db, doc["id"], today + timedelta(days=offset), DEFAULT_DURATION)
                )
            out.append(
                {
                    "doctorId": doc["id"],
                    "doctorName": doc["name"],
                    "specialty": doc["specialty"],
                    "slots": slots,
                }
            )
        return out


scheduler = Scheduler()


# ---------------------------------------------------------------------------
# Request payloads
# ---------------------------------------------------------------------------

class AppointmentCreate(BaseModel):
    patientId: str
    doctorId: str
    doctorName: Optional[str] = None
    specialty: Optional[str] = None
    dateTime: datetime
    type: str = "consultation"
    notes: Optional[str] = None
    reason: Optional[str] = None
    durationMinutes: Optional[int] = None


class ReschedulePayload(BaseModel):
    dateTime: Optional[datetime] = None
    status: Optional[
        Literal["scheduled", "confirmed", "pending", "completed", "cancelled"]
    ] = None


# ---------------------------------------------------------------------------
# Serialization & authorization helpers
# ---------------------------------------------------------------------------

def _serialize(a: Appointment) -> Dict[str, Any]:
    return {
        "id": a.id,
        "patientId": a.patient_id,
        "patientName": a.patient_name,
        "doctorId": a.doctor_id,
        "doctorName": a.doctor_name,
        "specialty": a.specialty,
        "dateTime": a.date_time.isoformat() if a.date_time else None,
        "durationMinutes": a.duration_minutes,
        "status": a.status,
        "type": a.type,
        "reason": a.reason,
        "notes": a.notes,
    }


def _can_act_on(current_user: User, appt: Appointment) -> bool:
    if current_user.role == "admin":
        return True
    if current_user.role == "doctor":
        return str(appt.doctor_id) == str(current_user.id)
    return str(appt.patient_id) == str(current_user.id)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/availability")
async def get_availability(
    specialty: Optional[str] = Query(None),
    doctor_name: Optional[str] = Query(None),
    days: int = Query(14, ge=1, le=30, description="Look-ahead window in days"),
    db: Session = Depends(get_db),
):
    """Return bookable availability per doctor.

    Slots are derived from clinic operating hours minus existing (non-cancelled)
    bookings, looking ahead ``days`` days. Filterable by specialty / doctor name.
    """
    return scheduler.get_availability(
        db, specialty=specialty, doctor_name=doctor_name, days=days
    )


@router.get("")
async def list_appointments(
    patient_id: Optional[str] = Query(None),
    doctor_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List appointments. Non-admins are constrained to their own appointments."""
    q = db.query(Appointment)

    if current_user.role == "patient":
        q = q.filter(Appointment.patient_id == str(current_user.id))
    elif current_user.role == "doctor":
        q = q.filter(Appointment.doctor_id == str(current_user.id))
        if patient_id:
            q = q.filter(Appointment.patient_id == patient_id)
    else:  # admin
        if patient_id:
            q = q.filter(Appointment.patient_id == patient_id)
        if doctor_id:
            q = q.filter(Appointment.doctor_id == doctor_id)

    rows = q.order_by(Appointment.date_time.asc()).all()
    return [_serialize(r) for r in rows]


@router.post("", status_code=201)
async def book_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book an appointment with DB-backed conflict detection."""
    if current_user.role == "patient" and str(payload.patientId) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Cannot book on behalf of another patient")

    duration = payload.durationMinutes or DEFAULT_DURATION

    if payload.dateTime < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot book appointments in the past")

    doctor = scheduler.resolve_doctor(
        db, doctor_id=payload.doctorId, doctor_name=payload.doctorName
    )
    if not doctor:
        raise HTTPException(status_code=404, detail="Requested doctor was not found")

    if not scheduler.is_within_clinic_hours(payload.dateTime, duration):
        raise HTTPException(
            status_code=400, detail="Requested time is outside clinic operating hours"
        )

    if scheduler.has_conflict(db, payload.doctorId, payload.dateTime, duration):
        next_slots = scheduler.next_available_slots(
            db, payload.doctorId, payload.dateTime, duration, count=5
        )
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Slot no longer available — please choose another time",
                "next_available_slots": next_slots,
            },
        )

    patient = db.query(User).filter(User.id == payload.patientId).first()

    appt = Appointment(
        patient_id=payload.patientId,
        patient_name=patient.full_name if patient else None,
        doctor_id=payload.doctorId,
        doctor_name=payload.doctorName or doctor.get("name"),
        specialty=payload.specialty or doctor.get("specialty"),
        date_time=payload.dateTime,
        duration_minutes=duration,
        type=payload.type,
        reason=payload.reason,
        notes=payload.notes,
        status="scheduled",
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return _serialize(appt)


@router.patch("/{appointment_id}")
async def reschedule_appointment(
    appointment_id: str,
    payload: ReschedulePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reschedule or update the status of an appointment (ownership enforced)."""
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if not _can_act_on(current_user, appt):
        raise HTTPException(status_code=403, detail="Not authorized to modify this appointment")

    if payload.dateTime is not None:
        if payload.dateTime < datetime.now():
            raise HTTPException(status_code=400, detail="Cannot reschedule into the past")
        if not scheduler.is_within_clinic_hours(payload.dateTime, appt.duration_minutes or DEFAULT_DURATION):
            raise HTTPException(
                status_code=400, detail="Requested time is outside clinic operating hours"
            )
        if scheduler.has_conflict(
            db, appt.doctor_id, payload.dateTime,
            appt.duration_minutes or DEFAULT_DURATION, exclude_id=appt.id,
        ):
            next_slots = scheduler.next_available_slots(
                db, appt.doctor_id, payload.dateTime,
                appt.duration_minutes or DEFAULT_DURATION, count=5,
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Slot no longer available — please choose another time",
                    "next_available_slots": next_slots,
                },
            )
        appt.date_time = payload.dateTime

    if payload.status is not None:
        appt.status = payload.status

    db.commit()
    db.refresh(appt)
    return _serialize(appt)


@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an appointment (ownership enforced; soft status change)."""
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if not _can_act_on(current_user, appt):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")
    appt.status = "cancelled"
    db.commit()
    return {"success": True}
