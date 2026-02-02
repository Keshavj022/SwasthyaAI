"""
Patient data models for Health Memory Agent.

Stores comprehensive patient medical history including:
- Patient profiles
- Visits/encounters
- Prescriptions
- Diagnoses
- Lab results
- Allergies

All records are versioned and timestamped for longitudinal tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, JSON, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime, date
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import Base


class Patient(Base):
    """
    Patient profile with demographics and basic information.
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    # Identifiers
    patient_id = Column(String(50), unique=True, index=True, nullable=False)  # External patient ID
    mrn = Column(String(50), unique=True, index=True)  # Medical Record Number

    # Demographics
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20))

    # Contact Information
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)

    # Emergency Contact
    emergency_contact_name = Column(String(200))
    emergency_contact_phone = Column(String(20))
    emergency_contact_relationship = Column(String(50))

    # Medical Information
    blood_type = Column(String(5))
    primary_language = Column(String(50), default="English")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)  # Soft delete flag

    # Relationships
    visits = relationship("Visit", back_populates="patient", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    diagnoses = relationship("Diagnosis", back_populates="patient", cascade="all, delete-orphan")
    allergies = relationship("Allergy", back_populates="patient", cascade="all, delete-orphan")
    lab_results = relationship("LabResult", back_populates="patient", cascade="all, delete-orphan")


class Visit(Base):
    """
    Patient visit/encounter record.
    Tracks all interactions with healthcare system.
    """
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # Visit Information
    visit_date = Column(DateTime, nullable=False, index=True)
    visit_type = Column(String(50))  # e.g., "routine", "urgent", "emergency", "followup"
    chief_complaint = Column(Text)

    # Vitals
    temperature = Column(Float)  # Celsius
    blood_pressure_systolic = Column(Integer)
    blood_pressure_diastolic = Column(Integer)
    heart_rate = Column(Integer)  # bpm
    respiratory_rate = Column(Integer)  # breaths per minute
    oxygen_saturation = Column(Float)  # percentage
    weight = Column(Float)  # kg
    height = Column(Float)  # cm
    bmi = Column(Float)

    # Visit Details
    symptoms = Column(JSON)  # List of symptoms
    physical_exam_findings = Column(Text)
    assessment = Column(Text)
    plan = Column(Text)
    provider_name = Column(String(200))
    provider_id = Column(String(50))

    # Status
    status = Column(String(20), default="completed")  # completed, scheduled, cancelled

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="visits")


class Prescription(Base):
    """
    Medication prescription record.
    Tracks current and historical medications.
    """
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # Medication Information
    medication_name = Column(String(200), nullable=False)
    generic_name = Column(String(200))
    dosage = Column(String(100))  # e.g., "500mg"
    route = Column(String(50))  # e.g., "oral", "IV", "topical"
    frequency = Column(String(100))  # e.g., "twice daily", "every 8 hours"
    duration = Column(String(100))  # e.g., "7 days", "ongoing"

    # Instructions
    instructions = Column(Text)
    indication = Column(String(500))  # Why prescribed

    # Dates
    prescribed_date = Column(Date, nullable=False, index=True)
    start_date = Column(Date)
    end_date = Column(Date)

    # Status
    status = Column(String(20), default="active")  # active, completed, discontinued, on_hold
    discontinued_reason = Column(String(500))

    # Prescriber
    prescriber_name = Column(String(200))
    prescriber_id = Column(String(50))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")


class Diagnosis(Base):
    """
    Patient diagnosis record.
    Tracks current and historical diagnoses with ICD codes.
    """
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # Diagnosis Information
    diagnosis_name = Column(String(500), nullable=False)
    icd10_code = Column(String(20), index=True)  # ICD-10 code
    diagnosis_type = Column(String(50))  # primary, secondary, chronic, acute

    # Clinical Details
    severity = Column(String(20))  # mild, moderate, severe
    clinical_notes = Column(Text)

    # Dates
    diagnosis_date = Column(Date, nullable=False, index=True)
    resolved_date = Column(Date)

    # Status
    status = Column(String(20), default="active")  # active, resolved, chronic, in_remission

    # Provider
    diagnosed_by = Column(String(200))
    provider_id = Column(String(50))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="diagnoses")


class Allergy(Base):
    """
    Patient allergy record.
    Critical for drug interaction checking.
    """
    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # Allergy Information
    allergen = Column(String(200), nullable=False)  # What they're allergic to
    allergen_type = Column(String(50))  # drug, food, environmental, other
    reaction = Column(String(500))  # What happens
    severity = Column(String(20))  # mild, moderate, severe, life_threatening

    # Dates
    onset_date = Column(Date)
    verified_date = Column(Date)

    # Status
    status = Column(String(20), default="active")  # active, resolved, unverified

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="allergies")


class LabResult(Base):
    """
    Laboratory test result record.
    Tracks all lab work with values and reference ranges.
    """
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # Test Information
    test_name = Column(String(200), nullable=False)
    test_code = Column(String(50))  # LOINC code
    category = Column(String(100))  # e.g., "chemistry", "hematology", "microbiology"

    # Results
    result_value = Column(String(100))
    result_unit = Column(String(50))
    reference_range = Column(String(100))
    flag = Column(String(20))  # normal, high, low, critical

    # Dates
    test_date = Column(DateTime, nullable=False, index=True)
    resulted_date = Column(DateTime)

    # Clinical Context
    clinical_notes = Column(Text)
    ordered_by = Column(String(200))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="lab_results")


class DocumentAttachment(Base):
    """
    Medical document attachments (images, PDFs, reports).
    References files stored on disk or in object storage.
    """
    __tablename__ = "document_attachments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # Document Information
    document_type = Column(String(50))  # xray, lab_report, prescription, insurance_card, etc.
    title = Column(String(500))
    description = Column(Text)

    # File Information
    file_path = Column(String(1000))  # Local file path
    file_name = Column(String(500))
    file_size = Column(Integer)  # bytes
    mime_type = Column(String(100))

    # Dates
    document_date = Column(Date)  # Date of the document (not upload date)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Metadata
    tags = Column(JSON)  # User-defined tags for searching

    # Foreign key (optional) - link to specific visit
    visit_id = Column(Integer, ForeignKey("visits.id"), nullable=True)
