"""Appointment model for patient–doctor scheduling."""

from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime, timezone
import uuid
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, index=True, nullable=False)
    doctor_id = Column(String, index=True, nullable=False)
    doctor_name = Column(String, nullable=True)
    specialty = Column(String, nullable=True)
    date_time = Column(DateTime, nullable=False)
    status = Column(String, default="scheduled", nullable=False)
    type = Column(String, nullable=False, default="consultation")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
