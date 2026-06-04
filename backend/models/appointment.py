"""Appointment model for patient–doctor scheduling."""

from sqlalchemy import Column, String, DateTime, Text, Integer, Index
from datetime import datetime, timezone
import uuid
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Patient/doctor linkage. patient_id/doctor_id reference User.id so both ends
    # are resolvable to a full_name; *_name columns are denormalised snapshots so
    # the schedule still renders if a profile is later edited/removed.
    patient_id = Column(String, index=True, nullable=False)
    patient_name = Column(String, nullable=True)
    doctor_id = Column(String, index=True, nullable=False)
    doctor_name = Column(String, nullable=True)
    specialty = Column(String, nullable=True)

    date_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=30)
    status = Column(String, default="scheduled", nullable=False)
    type = Column(String, nullable=False, default="consultation")
    reason = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Conflict guard: a doctor cannot hold two appointments at the exact same
    # start time. Application-level overlap detection covers partial overlaps;
    # this index also speeds up per-doctor schedule lookups. (SQLite-compatible;
    # cancelled rows keep their slot but are excluded by application logic.)
    __table_args__ = (
        Index("ix_appointments_doctor_datetime", "doctor_id", "date_time"),
    )
