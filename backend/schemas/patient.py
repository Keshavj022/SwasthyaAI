"""
Pydantic schemas for Patient Data API.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, date


# Patient Schemas

class PatientCreate(BaseModel):
    """Schema for creating a new patient"""
    patient_id: str = Field(..., description="Unique patient identifier")
    mrn: Optional[str] = Field(None, description="Medical Record Number")
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    blood_type: Optional[str] = None
    primary_language: str = "English"


class PatientUpdate(BaseModel):
    """Schema for updating patient information"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None


class PatientResponse(BaseModel):
    """Schema for patient response"""
    id: int
    patient_id: str
    mrn: Optional[str]
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Optional[str]
    blood_type: Optional[str]
    created_at: datetime
    active: bool

    class Config:
        from_attributes = True


# Visit Schemas

class VisitCreate(BaseModel):
    """Schema for creating a visit record"""
    patient_id: str
    visit_date: datetime
    visit_type: str
    chief_complaint: Optional[str] = None
    temperature: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    symptoms: Optional[List[str]] = None
    physical_exam_findings: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    provider_name: Optional[str] = None
    provider_id: Optional[str] = None


class VisitResponse(BaseModel):
    """Schema for visit response"""
    id: int
    visit_date: datetime
    visit_type: str
    chief_complaint: Optional[str]
    provider_name: Optional[str]
    status: str

    class Config:
        from_attributes = True


# Prescription Schemas

class PrescriptionCreate(BaseModel):
    """Schema for creating a prescription"""
    patient_id: str
    medication_name: str
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    indication: Optional[str] = None
    prescribed_date: date
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prescriber_name: Optional[str] = None
    prescriber_id: Optional[str] = None


class PrescriptionUpdate(BaseModel):
    """Schema for updating prescription"""
    status: Optional[str] = None
    discontinued_reason: Optional[str] = None
    end_date: Optional[date] = None


class PrescriptionResponse(BaseModel):
    """Schema for prescription response"""
    id: int
    medication_name: str
    dosage: Optional[str]
    frequency: Optional[str]
    status: str
    prescribed_date: date

    class Config:
        from_attributes = True


# Diagnosis Schemas

class DiagnosisCreate(BaseModel):
    """Schema for creating a diagnosis"""
    patient_id: str
    diagnosis_name: str
    icd10_code: Optional[str] = None
    diagnosis_type: Optional[str] = None
    severity: Optional[str] = None
    clinical_notes: Optional[str] = None
    diagnosis_date: date
    diagnosed_by: Optional[str] = None
    provider_id: Optional[str] = None


class DiagnosisUpdate(BaseModel):
    """Schema for updating diagnosis"""
    status: Optional[str] = None
    severity: Optional[str] = None
    clinical_notes: Optional[str] = None
    resolved_date: Optional[date] = None


class DiagnosisResponse(BaseModel):
    """Schema for diagnosis response"""
    id: int
    diagnosis_name: str
    icd10_code: Optional[str]
    status: str
    diagnosis_date: date

    class Config:
        from_attributes = True


# Allergy Schemas

class AllergyCreate(BaseModel):
    """Schema for creating an allergy record"""
    patient_id: str
    allergen: str
    allergen_type: Optional[str] = None
    reaction: Optional[str] = None
    severity: Optional[str] = None
    onset_date: Optional[date] = None


class AllergyResponse(BaseModel):
    """Schema for allergy response"""
    id: int
    allergen: str
    allergen_type: Optional[str]
    reaction: Optional[str]
    severity: Optional[str]
    status: str

    class Config:
        from_attributes = True


# Timeline Schemas

class TimelineResponse(BaseModel):
    """Schema for patient timeline"""
    patient_id: str
    patient_name: str
    timeline_period: str
    total_events: int
    events: List[Dict[str, Any]]


class PatientSummaryResponse(BaseModel):
    """Schema for patient summary"""
    patient_info: Dict[str, Any]
    active_prescriptions: List[Dict[str, Any]]
    active_diagnoses: List[Dict[str, Any]]
    allergies: List[Dict[str, Any]]
    recent_visits: List[Dict[str, Any]]
