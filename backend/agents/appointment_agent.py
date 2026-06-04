"""
Appointment & Hospital Operations Agent (DB-backed)

This agent handles appointment scheduling, doctor availability, and follow-ups.
It is NOT a medical AI agent — it provides administrative/operational support.

Persistence & conflict detection are delegated to the shared scheduler in
``routers/appointments.py`` so that EVERY scheduling decision operates on the same
SQLAlchemy ``Appointment`` table used by the REST endpoints. There is no
in-memory appointment list any more — bookings made via the orchestrator and via
the REST API share one source of truth.

Safety Notes:
- This agent does NOT provide medical advice or diagnoses.
- All appointments must be confirmed by clinic staff.
- Emergency cases should be directed to Triage Agent first.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse

logger = logging.getLogger(__name__)


class AppointmentAgent(BaseAgent):
    """Administrative agent for appointment scheduling backed by the database."""

    def __init__(self):
        super().__init__()

        # Standard appointment-type durations (minutes).
        self.appointment_types = {
            "initial_consultation": {"duration": 60, "requires_prep": True},
            "consultation": {"duration": 30, "requires_prep": False},
            "follow_up": {"duration": 30, "requires_prep": False},
            "routine_checkup": {"duration": 30, "requires_prep": True},
            "urgent_care": {"duration": 45, "requires_prep": False},
            "procedure": {"duration": 90, "requires_prep": True},
            "telemedicine": {"duration": 20, "requires_prep": False},
        }

    # ------------------------------------------------------------------
    # Registry metadata
    # ------------------------------------------------------------------

    def get_capabilities(self) -> List[str]:
        return [
            "appointment", "schedule", "book", "availability",
            "reschedule", "cancel", "follow-up", "available",
            "doctor available", "clinic hours", "telemedicine",
            "virtual appointment", "urgent care",
        ]

    def get_description(self) -> str:
        return (
            "Appointment scheduling and hospital operations — booking, "
            "cancellations, doctor availability, and follow-ups (DB-backed)"
        )

    def get_confidence_threshold(self) -> float:
        return 0.70

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _db(self):
        """Open a fresh DB session. Caller is responsible for closing it."""
        from database import SessionLocal
        return SessionLocal()

    def _scheduler(self):
        from routers.appointments import scheduler
        return scheduler

    def _duration_for(self, appointment_type: str) -> int:
        meta = self.appointment_types.get(appointment_type)
        return meta["duration"] if meta else 30

    def _parse_datetime(self, date_str: Optional[str], time_str: Optional[str]) -> Optional[datetime]:
        # Accept either a full ISO datetime in `date_str`, or date + time parts.
        if date_str and not time_str:
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                pass
        if date_str and time_str:
            try:
                return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except ValueError:
                return None
        return None

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    async def process(self, request: AgentRequest) -> AgentResponse:
        # Support both the legacy `task` key and the UI's `intent` key.
        task = request.context.get("task") or request.context.get("intent") or "book_appointment"
        task = {
            "book_appointment": "book_appointment",
            "check_availability": "check_availability",
            "availability": "check_availability",
            "reschedule": "reschedule",
            "reschedule_appointment": "reschedule",
            "cancel": "cancel",
            "cancel_appointment": "cancel",
            "list_appointments": "list_appointments",
            "list": "list_appointments",
        }.get(task, task)

        handlers = {
            "book_appointment": self._book_appointment,
            "check_availability": self._check_availability,
            "reschedule": self._reschedule_appointment,
            "cancel": self._cancel_appointment,
            "list_appointments": self._list_appointments,
        }
        handler = handlers.get(task)
        if not handler:
            return AgentResponse(
                agent_name="appointment",
                success=False,
                confidence=0.0,
                data={"error": f"Unknown task: {task}", "stub_mode": False,
                      "supported_tasks": list(handlers.keys())},
                reasoning="Task not recognized",
            )
        return await handler(request)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    async def _book_appointment(self, request: AgentRequest) -> AgentResponse:
        from models.appointment import Appointment
        from models.user import User

        patient_id = request.user_id
        ctx = request.context
        doctor_id = ctx.get("doctor_id")
        doctor_name = ctx.get("doctor_name")
        specialty = ctx.get("specialty")
        appt_type = ctx.get("appointment_type") or ctx.get("type") or "consultation"
        duration = self._duration_for(appt_type)
        reason = ctx.get("reason", "")

        requested = self._parse_datetime(
            ctx.get("requested_date") or ctx.get("preferred_date"),
            ctx.get("preferred_time"),
        )
        if requested is None:
            return AgentResponse(
                agent_name="appointment", success=False, confidence=0.0,
                data={"error": "Invalid or missing date/time", "stub_mode": False,
                      "expected": "ISO datetime in requested_date, or preferred_date + preferred_time"},
                reasoning="Date/time parsing failed",
            )

        db = self._db()
        try:
            scheduler = self._scheduler()

            if requested < datetime.now():
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.0,
                    data={"error": "Cannot book appointments in the past", "stub_mode": False},
                    reasoning="Past date requested",
                )

            doctor = scheduler.resolve_doctor(db, doctor_id=doctor_id, doctor_name=doctor_name)
            if not doctor and specialty:
                matches = scheduler.list_doctors(db, specialty=specialty)
                doctor = matches[0] if matches else None
            if not doctor:
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.0,
                    data={"error": "No matching doctor found", "stub_mode": False},
                    reasoning="Doctor not resolved",
                )

            if not scheduler.is_within_clinic_hours(requested, duration):
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.5,
                    data={"error": "Requested time is outside clinic operating hours",
                          "stub_mode": False},
                    reasoning="Outside clinic hours",
                )

            if scheduler.has_conflict(db, doctor["id"], requested, duration):
                next_slots = scheduler.next_available_slots(db, doctor["id"], requested, duration, count=5)
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.5,
                    data={"error": "Time slot already booked",
                          "next_available_slots": next_slots, "stub_mode": False},
                    reasoning="Scheduling conflict detected",
                )

            patient = db.query(User).filter(User.id == patient_id).first()
            appt = Appointment(
                patient_id=patient_id,
                patient_name=patient.full_name if patient else None,
                doctor_id=doctor["id"],
                doctor_name=doctor["name"],
                specialty=specialty or doctor.get("specialty"),
                date_time=requested,
                duration_minutes=duration,
                type=appt_type,
                reason=reason,
                status="scheduled",
            )
            db.add(appt)
            db.commit()
            db.refresh(appt)

            return AgentResponse(
                agent_name="appointment", success=True, confidence=1.0,
                data={
                    "stub_mode": False,
                    "appointment": self._serialize(appt),
                    "confirmation_message": f"Appointment booked with {doctor['name']}",
                    "preparation_required": self.appointment_types.get(appt_type, {}).get("requires_prep", False),
                },
                reasoning=f"Successfully scheduled {appt_type} appointment",
            )
        finally:
            db.close()

    async def _check_availability(self, request: AgentRequest) -> AgentResponse:
        ctx = request.context
        db = self._db()
        try:
            availability = self._scheduler().get_availability(
                db,
                specialty=ctx.get("specialty"),
                doctor_name=ctx.get("doctor_name"),
                days=int(ctx.get("days", 14)),
            )
            return AgentResponse(
                agent_name="appointment", success=True, confidence=1.0,
                data={"availability": availability, "total_doctors": len(availability),
                      "stub_mode": False},
                reasoning="Retrieved availability from the schedule",
            )
        finally:
            db.close()

    async def _reschedule_appointment(self, request: AgentRequest) -> AgentResponse:
        from models.appointment import Appointment

        ctx = request.context
        appointment_id = ctx.get("appointment_id")
        new_dt = self._parse_datetime(
            ctx.get("new_date") or ctx.get("requested_date"), ctx.get("new_time")
        )

        db = self._db()
        try:
            appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            if not appt:
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.0,
                    data={"error": "Appointment not found", "stub_mode": False},
                    reasoning="Invalid appointment ID",
                )
            # Ownership: a patient may only reschedule their own appointment.
            if str(appt.patient_id) != str(request.user_id) and request.context.get("user_type") == "patient":
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.0,
                    data={"error": "Not authorized to modify this appointment", "stub_mode": False},
                    reasoning="Ownership check failed",
                )
            if appt.status == "cancelled":
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.0,
                    data={"error": "Cannot reschedule a cancelled appointment", "stub_mode": False},
                    reasoning="Appointment already cancelled",
                )
            if new_dt is None or new_dt < datetime.now():
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.0,
                    data={"error": "Invalid or past new date/time", "stub_mode": False},
                    reasoning="Bad reschedule target",
                )

            scheduler = self._scheduler()
            duration = appt.duration_minutes or 30
            if not scheduler.is_within_clinic_hours(new_dt, duration):
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.5,
                    data={"error": "Requested time is outside clinic operating hours",
                          "stub_mode": False},
                    reasoning="Outside clinic hours",
                )
            if scheduler.has_conflict(db, appt.doctor_id, new_dt, duration, exclude_id=appt.id):
                next_slots = scheduler.next_available_slots(db, appt.doctor_id, new_dt, duration, count=5)
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.5,
                    data={"error": "Time slot already booked",
                          "next_available_slots": next_slots, "stub_mode": False},
                    reasoning="Scheduling conflict detected",
                )

            appt.date_time = new_dt
            appt.status = "scheduled"
            db.commit()
            db.refresh(appt)
            return AgentResponse(
                agent_name="appointment", success=True, confidence=1.0,
                data={"message": "Appointment rescheduled successfully",
                      "appointment": self._serialize(appt), "stub_mode": False},
                reasoning="Successfully rescheduled appointment",
            )
        finally:
            db.close()

    async def _cancel_appointment(self, request: AgentRequest) -> AgentResponse:
        from models.appointment import Appointment

        appointment_id = request.context.get("appointment_id")
        db = self._db()
        try:
            appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            if not appt:
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.0,
                    data={"error": "Appointment not found", "stub_mode": False},
                    reasoning="Invalid appointment ID",
                )
            if str(appt.patient_id) != str(request.user_id) and request.context.get("user_type") == "patient":
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.0,
                    data={"error": "Not authorized to cancel this appointment", "stub_mode": False},
                    reasoning="Ownership check failed",
                )
            if appt.status == "cancelled":
                return AgentResponse(
                    agent_name="appointment", success=False, confidence=0.0,
                    data={"error": "Appointment already cancelled", "stub_mode": False},
                    reasoning="Appointment already cancelled",
                )
            appt.status = "cancelled"
            db.commit()
            return AgentResponse(
                agent_name="appointment", success=True, confidence=1.0,
                data={"message": "Appointment cancelled successfully",
                      "refund_policy": "Cancellations made 24+ hours in advance are fully refundable",
                      "stub_mode": False},
                reasoning="Successfully cancelled appointment",
            )
        finally:
            db.close()

    async def _list_appointments(self, request: AgentRequest) -> AgentResponse:
        from models.appointment import Appointment

        patient_id = request.user_id
        status_filter = request.context.get("status", "all")
        db = self._db()
        try:
            q = db.query(Appointment).filter(Appointment.patient_id == patient_id)
            if status_filter != "all":
                q = q.filter(Appointment.status == status_filter)
            rows = q.order_by(Appointment.date_time.asc()).all()

            now = datetime.now()
            upcoming, past = [], []
            for r in rows:
                serialized = self._serialize(r)
                if r.date_time and r.date_time >= now and r.status not in ("cancelled", "completed"):
                    upcoming.append(serialized)
                else:
                    past.append(serialized)

            return AgentResponse(
                agent_name="appointment", success=True, confidence=1.0,
                data={
                    "stub_mode": False,
                    "upcoming_appointments": upcoming,
                    "past_appointments": past,
                    "total_appointments": len(rows),
                    "upcoming_count": len(upcoming),
                    "past_count": len(past),
                },
                reasoning=f"Retrieved {len(rows)} appointments",
            )
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def _serialize(self, a) -> Dict[str, Any]:
        return {
            "appointment_id": a.id,
            "patient_id": a.patient_id,
            "patient_name": a.patient_name,
            "doctor_id": a.doctor_id,
            "doctor_name": a.doctor_name,
            "specialty": a.specialty,
            "date_time": a.date_time.isoformat() if a.date_time else None,
            "duration_minutes": a.duration_minutes,
            "type": a.type,
            "status": a.status,
            "reason": a.reason,
            "notes": a.notes,
        }
