"""
System models for health monitoring and audit logs.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from backend.database import Base


class SystemHealth(Base):
    """Track system health checks and status"""

    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="healthy")
    details = Column(JSON, nullable=True)


class AuditLog(Base):
    """Audit trail for all AI interactions (SAFETY_AND_SCOPE.md §7.2)"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String, index=True)  # Clinician or patient ID
    agent_name = Column(String)  # Which agent was invoked
    action = Column(String)  # Type of action
    input_data = Column(JSON)  # De-identified input
    output_data = Column(JSON)  # AI output generated
    confidence_score = Column(Integer, nullable=True)  # 0-100
    escalation_triggered = Column(String, nullable=True)  # Red-flag type if any
    clinician_override = Column(String, nullable=True)  # Override reason
