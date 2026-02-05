"""
Health Monitoring models for Health Support Agent.
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, JSON, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import Base

class CheckIn(Base):
    """Daily wellness check-in record"""
    __tablename__ = "check_ins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    
    date = Column(Date, nullable=False, index=True)
    time = Column(String(5))  # HH:MM
    
    mood = Column(Integer)  # 1-10
    energy_level = Column(Integer)  # 1-10
    sleep_hours = Column(Float)
    pain_level = Column(Integer)  # 1-10
    
    symptoms = Column(JSON)  # List of symptoms
    
    timestamp = Column(DateTime, default=datetime.utcnow)

class ConditionLog(Base):
    """Chronic condition tracking log"""
    __tablename__ = "condition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    
    condition = Column(String, index=True, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(String(5))
    
    metrics = Column(JSON)  # specific metrics for condition
    notes = Column(Text)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

class HealthGoal(Base):
    """User health goals"""
    __tablename__ = "health_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    
    category = Column(String)  # exercise, diet, sleep, etc.
    goal_type = Column(String) # steps, calories, etc.
    target = Column(Float)
    frequency = Column(String) # daily, weekly
    
    start_date = Column(Date)
    active = Column(Boolean, default=True)
    
    progress = Column(JSON, default=list) # List of progress entries

class Reminder(Base):
    """Medication and Appointment reminders"""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    
    type = Column(String)  # medication, appointment
    
    # Medication specific
    medication = Column(String, nullable=True)
    dosage = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    times = Column(JSON, nullable=True)  # List of times ["09:00", "20:00"]
    condition = Column(String, nullable=True)
    
    # Appointment specific
    description = Column(String, nullable=True)
    date = Column(Date, nullable=True)
    time = Column(String, nullable=True)
    specialty = Column(String, nullable=True)
    
    active = Column(Boolean, default=True)

class SymptomLog(Base):
    """Longitudinal symptom tracking"""
    __tablename__ = "symptom_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    
    date = Column(Date, nullable=False)
    time = Column(String(5))
    
    symptoms = Column(JSON) # List of symptoms
    severity = Column(Integer)
    duration = Column(String)
    notes = Column(Text)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
