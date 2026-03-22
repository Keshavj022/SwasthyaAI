from database import Base
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON
from sqlalchemy.sql import func
import uuid


class SavedLabResult(Base):
    __tablename__ = "saved_lab_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, nullable=False, index=True)
    report_date = Column(String, nullable=False)
    lab_name = Column(String, default="")
    test_count = Column(Integer, default=0)
    has_critical = Column(Boolean, default=False)
    results_json = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
