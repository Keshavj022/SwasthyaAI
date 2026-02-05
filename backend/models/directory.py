"""
Doctor Directory models for Nearby Doctors Agent.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float, JSON
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import Base

class Doctor(Base):
    """Doctor directory entry"""
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(String, unique=True, index=True)
    
    name = Column(String, nullable=False)
    specialty = Column(String, index=True, nullable=False)
    credentials = Column(String)
    
    address = Column(String)
    zip_code = Column(String, index=True)
    phone = Column(String)
    
    accepting_new_patients = Column(Boolean, default=True)
    insurance_accepted = Column(JSON) # List of insurance providers
    languages = Column(JSON) # List of languages spoken
    
    rating = Column(Float)
    years_experience = Column(Integer)
    hospital_affiliations = Column(JSON)
    
    # Coordinates for distance calc (in production use PostGIS or similar)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
