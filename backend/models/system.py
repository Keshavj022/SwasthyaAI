"""
System models for health monitoring and audit logs.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path to import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Base


class SystemHealth(Base):
    """Track system health checks and status"""

    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="healthy")
    details = Column(JSON, nullable=True)


class AuditLog(Base):
    """
    Audit trail for all AI interactions (SAFETY_AND_SCOPE.md §7.2)

    Enhanced with explainability fields for transparency and review:
    - reasoning_summary: Human-readable explanation of AI decision
    - decision_factors: Key factors that influenced the outcome
    - alternative_considerations: Other options that were considered
    - explainability_score: How transparent/explainable this decision was (0-100)
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String, index=True)  # Clinician or patient ID (hashed)
    agent_name = Column(String, index=True)  # Which agent was invoked
    action = Column(String)  # Type of action (agent_query, safety_violation, etc.)

    # Input/Output
    input_data = Column(JSON)  # De-identified input
    output_data = Column(JSON)  # AI output generated

    # Confidence and Quality
    confidence_score = Column(Integer, nullable=True)  # 0-100
    explainability_score = Column(Integer, nullable=True)  # 0-100

    # Explainability Fields (Enhanced)
    reasoning_summary = Column(String, nullable=True)  # Human-readable explanation
    decision_factors = Column(JSON, nullable=True)  # Key factors influencing decision
    alternative_considerations = Column(JSON, nullable=True)  # Other options considered

    # Safety and Escalation
    escalation_triggered = Column(String, nullable=True)  # Red-flag type if any
    safety_flags = Column(JSON, nullable=True)  # Any safety concerns detected

    # Human Review
    clinician_override = Column(String, nullable=True)  # Override reason
    reviewed_by = Column(String, nullable=True)  # Clinician who reviewed (hashed)
    review_timestamp = Column(DateTime, nullable=True)  # When reviewed
    review_notes = Column(String, nullable=True)  # Clinician's notes
