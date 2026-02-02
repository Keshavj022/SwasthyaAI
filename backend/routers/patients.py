"""
Patient Data API - CRUD endpoints for Health Memory Agent.

Provides comprehensive patient data management:
- Patient profiles
- Visits/encounters
- Prescriptions
- Diagnoses
- Allergies
- Timeline and history retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models.patient import Patient, Visit, Prescription, Diagnosis, Allergy
from schemas.patient import (
    PatientCreate, PatientUpdate, PatientResponse,
    VisitCreate, VisitResponse,
    PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse,
    DiagnosisCreate, DiagnosisUpdate, DiagnosisResponse,
    AllergyCreate, AllergyResponse,
    TimelineResponse, PatientSummaryResponse
)
from agents.health_memory_agent import HealthMemoryAgent

router = APIRouter(prefix="/patients", tags=["patients"])

# Initialize health memory agent
_health_memory = HealthMemoryAgent()


# ==================== PATIENT CRUD ====================

@router.post("", response_model=PatientResponse)
async def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new patient profile.

    Args:
        patient: Patient creation data

    Returns:
        Created patient record

    Example:
        ```json
        {
            "patient_id": "P12345",
            "mrn": "MRN001",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-05-15",
            "gender": "M",
            "blood_type": "A+"
        }
        ```
    """
    # Check if patient already exists
    existing = db.query(Patient).filter(Patient.patient_id == patient.patient_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Patient with ID '{patient.patient_id}' already exists")

    # Create patient
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    return db_patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get patient by ID.

    Args:
        patient_id: Patient identifier

    Returns:
        Patient record

    Raises:
        404: Patient not found
    """
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db)
):
    """
    Update patient information.

    Args:
        patient_id: Patient identifier
        patient_update: Fields to update

    Returns:
        Updated patient record
    """
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    # Update fields
    update_data = patient_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)

    db.commit()
    db.refresh(patient)

    return patient


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    hard_delete: bool = Query(False, description="Permanently delete (true) or soft delete (false)"),
    db: Session = Depends(get_db)
):
    """
    Delete patient record.

    Args:
        patient_id: Patient identifier
        hard_delete: If true, permanently deletes. If false, soft deletes (sets active=False)

    Returns:
        Confirmation message
    """
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    if hard_delete:
        db.delete(patient)
        message = "Patient permanently deleted"
    else:
        patient.active = False
        message = "Patient soft deleted (set to inactive)"

    db.commit()

    return {"message": message, "patient_id": patient_id}


# ==================== PATIENT SUMMARY & TIMELINE ====================

@router.get("/{patient_id}/summary", response_model=PatientSummaryResponse)
async def get_patient_summary(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive patient summary.

    Includes:
    - Demographics
    - Active prescriptions
    - Active diagnoses
    - Allergies
    - Recent visits (last 6 months)

    Args:
        patient_id: Patient identifier

    Returns:
        Complete patient summary
    """
    summary = _health_memory.get_patient_summary(db, patient_id)

    if not summary:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    return summary


@router.get("/{patient_id}/timeline", response_model=TimelineResponse)
async def get_patient_timeline(
    patient_id: str,
    months: int = Query(12, ge=1, le=60, description="Number of months to include"),
    db: Session = Depends(get_db)
):
    """
    Get chronological timeline of all patient events.

    Args:
        patient_id: Patient identifier
        months: Number of months to include (default: 12)

    Returns:
        Timeline with all events (visits, prescriptions, diagnoses, labs)

    Example:
        ```
        GET /api/patients/P12345/timeline?months=6
        ```
    """
    timeline = _health_memory.get_patient_timeline(db, patient_id, months)

    if not timeline:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    return timeline


@router.get("/{patient_id}/search")
async def search_patient_history(
    patient_id: str,
    query: str = Query(..., min_length=2, description="Search term"),
    db: Session = Depends(get_db)
):
    """
    Search patient history for specific term.

    Searches across:
    - Visit records (chief complaint, assessment)
    - Prescriptions (medication names)
    - Diagnoses
    - Lab results

    Args:
        patient_id: Patient identifier
        query: Search term

    Returns:
        Search results grouped by category

    Example:
        ```
        GET /api/patients/P12345/search?query=aspirin
        ```
    """
    results = _health_memory.search_history(db, patient_id, query)

    if not results:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    return results


# ==================== VISITS ====================

@router.post("/{patient_id}/visits", response_model=VisitResponse)
async def create_visit(
    patient_id: str,
    visit: VisitCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new visit record.

    Args:
        patient_id: Patient identifier
        visit: Visit data

    Returns:
        Created visit record
    """
    # Verify patient exists
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    # Create visit
    visit_data = visit.dict()
    visit_data["patient_id"] = patient.id  # Use internal ID
    db_visit = Visit(**visit_data)

    # Calculate BMI if height and weight provided
    if db_visit.height and db_visit.weight:
        height_m = db_visit.height / 100  # Convert cm to m
        db_visit.bmi = round(db_visit.weight / (height_m ** 2), 2)

    db.add(db_visit)
    db.commit()
    db.refresh(db_visit)

    return db_visit


@router.get("/{patient_id}/visits", response_model=List[VisitResponse])
async def list_visits(
    patient_id: str,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List patient visits (most recent first).

    Args:
        patient_id: Patient identifier
        limit: Maximum number of visits to return

    Returns:
        List of visits
    """
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    visits = db.query(Visit).filter(
        Visit.patient_id == patient.id
    ).order_by(Visit.visit_date.desc()).limit(limit).all()

    return visits


# ==================== PRESCRIPTIONS ====================

@router.post("/{patient_id}/prescriptions", response_model=PrescriptionResponse)
async def create_prescription(
    patient_id: str,
    prescription: PrescriptionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new prescription record.

    Args:
        patient_id: Patient identifier
        prescription: Prescription data

    Returns:
        Created prescription record
    """
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    prescription_data = prescription.dict()
    prescription_data["patient_id"] = patient.id
    db_prescription = Prescription(**prescription_data)

    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)

    return db_prescription


@router.get("/{patient_id}/prescriptions", response_model=List[PrescriptionResponse])
async def list_prescriptions(
    patient_id: str,
    status: Optional[str] = Query(None, description="Filter by status (active, completed, discontinued)"),
    db: Session = Depends(get_db)
):
    """
    List patient prescriptions.

    Args:
        patient_id: Patient identifier
        status: Optional status filter

    Returns:
        List of prescriptions
    """
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    query = db.query(Prescription).filter(Prescription.patient_id == patient.id)

    if status:
        query = query.filter(Prescription.status == status)

    prescriptions = query.order_by(Prescription.prescribed_date.desc()).all()

    return prescriptions


@router.patch("/{patient_id}/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
async def update_prescription(
    patient_id: str,
    prescription_id: int,
    prescription_update: PrescriptionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update prescription (typically to discontinue or change status).

    Args:
        patient_id: Patient identifier
        prescription_id: Prescription ID
        prescription_update: Fields to update

    Returns:
        Updated prescription
    """
    prescription = db.query(Prescription).join(Patient).filter(
        Patient.patient_id == patient_id,
        Prescription.id == prescription_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    update_data = prescription_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prescription, key, value)

    db.commit()
    db.refresh(prescription)

    return prescription


# ==================== DIAGNOSES ====================

@router.post("/{patient_id}/diagnoses", response_model=DiagnosisResponse)
async def create_diagnosis(
    patient_id: str,
    diagnosis: DiagnosisCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new diagnosis record.

    Args:
        patient_id: Patient identifier
        diagnosis: Diagnosis data

    Returns:
        Created diagnosis record
    """
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    diagnosis_data = diagnosis.dict()
    diagnosis_data["patient_id"] = patient.id
    db_diagnosis = Diagnosis(**diagnosis_data)

    db.add(db_diagnosis)
    db.commit()
    db.refresh(db_diagnosis)

    return db_diagnosis


@router.get("/{patient_id}/diagnoses", response_model=List[DiagnosisResponse])
async def list_diagnoses(
    patient_id: str,
    status: Optional[str] = Query(None, description="Filter by status (active, resolved, chronic)"),
    db: Session = Depends(get_db)
):
    """
    List patient diagnoses.

    Args:
        patient_id: Patient identifier
        status: Optional status filter

    Returns:
        List of diagnoses
    """
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    query = db.query(Diagnosis).filter(Diagnosis.patient_id == patient.id)

    if status:
        query = query.filter(Diagnosis.status == status)

    diagnoses = query.order_by(Diagnosis.diagnosis_date.desc()).all()

    return diagnoses


# ==================== ALLERGIES ====================

@router.post("/{patient_id}/allergies", response_model=AllergyResponse)
async def create_allergy(
    patient_id: str,
    allergy: AllergyCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new allergy record.

    IMPORTANT: Allergies are critical for drug safety checks.

    Args:
        patient_id: Patient identifier
        allergy: Allergy data

    Returns:
        Created allergy record
    """
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    allergy_data = allergy.dict()
    allergy_data["patient_id"] = patient.id
    db_allergy = Allergy(**allergy_data)

    db.add(db_allergy)
    db.commit()
    db.refresh(db_allergy)

    return db_allergy


@router.get("/{patient_id}/allergies", response_model=List[AllergyResponse])
async def list_allergies(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    List patient allergies.

    CRITICAL for drug interaction checking.

    Args:
        patient_id: Patient identifier

    Returns:
        List of allergies
    """
    allergies = _health_memory.get_allergies(db, patient_id)

    if allergies is None:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    return allergies
