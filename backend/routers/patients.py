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
from pydantic import BaseModel, field_validator
import sys
from pathlib import Path
from datetime import date as date_type

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models.health_monitoring import CheckIn
from models.patient import Patient, Visit, Prescription, Diagnosis, Allergy
from models.user import User
from services.auth_service import get_current_user
from schemas.patient import (
    PatientCreate, PatientUpdate, PatientResponse,
    VisitCreate, VisitResponse,
    PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse,
    DiagnosisCreate, DiagnosisUpdate, DiagnosisResponse,
    AllergyCreate, AllergyResponse,
    TimelineResponse, PatientSummaryResponse
)
from agents.health_memory_agent import HealthMemoryAgent


def _ensure_can_access_patient(current_user: User, patient_id: str) -> None:
    """Object-level authorization for patient-scoped data.

    - Doctors and admins may access any patient record.
    - A patient may ONLY access their own record. The frontend uses the User UUID
      (current_user.id) as the patient identifier, so a patient is authorized iff
      the requested patient_id matches their own id.

    Raises 403 (not 404) so the existence of other records is not leaked, while
    still allowing the handler's own 404 for truly-missing records the user owns.
    """
    if current_user.role in ("doctor", "admin"):
        return
    if str(patient_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this patient record")


class CheckInCreate(BaseModel):
    mood: Optional[int] = None       # 1-10
    energy: Optional[int] = None     # 1-10
    sleep: Optional[float] = None    # hours
    symptoms: List[str] = []
    painLevel: Optional[int] = None  # 1-10

    @field_validator("mood", "energy", "painLevel")
    @classmethod
    def _scale_1_10(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v < 1 or v > 10:
            raise ValueError("Value must be between 1 and 10")
        return v

    @field_validator("sleep")
    @classmethod
    def _sleep_bounds(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if v < 0 or v > 24:
            raise ValueError("Sleep hours must be between 0 and 24")
        return v

    @field_validator("symptoms")
    @classmethod
    def _symptoms_bounds(cls, v: List[str]) -> List[str]:
        if v and len(v) > 50:
            raise ValueError("Too many symptoms (max 50)")
        return v


router = APIRouter(prefix="/patients", tags=["patients"])

# Initialize health memory agent
_health_memory = HealthMemoryAgent()


# ==================== PATIENT CRUD ====================

@router.post("", response_model=PatientResponse)
async def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    # Creating patient profiles is a clinical/admin operation.
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to create patient records")

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get patient by ID.

    Args:
        patient_id: Patient identifier

    Returns:
        Patient record

    Raises:
        403: Patient may only access their own record
        404: Patient not found
    """
    _ensure_can_access_patient(current_user, patient_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update patient information.

    Args:
        patient_id: Patient identifier
        patient_update: Fields to update

    Returns:
        Updated patient record
    """
    _ensure_can_access_patient(current_user, patient_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete patient record.

    Only doctors and admins may delete patient records.

    Args:
        patient_id: Patient identifier
        hard_delete: If true, permanently deletes. If false, soft deletes (sets active=False)

    Returns:
        Confirmation message
    """
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete patient records")
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    _ensure_can_access_patient(current_user, patient_id)
    summary = _health_memory.get_patient_summary(db, patient_id)

    if not summary:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    return summary


@router.get("/{patient_id}/timeline", response_model=TimelineResponse)
async def get_patient_timeline(
    patient_id: str,
    months: int = Query(12, ge=1, le=60, description="Number of months to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    _ensure_can_access_patient(current_user, patient_id)
    timeline = _health_memory.get_patient_timeline(db, patient_id, months)

    if not timeline:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    return timeline


@router.get("/{patient_id}/search")
async def search_patient_history(
    patient_id: str,
    query: str = Query(..., min_length=2, description="Search term"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    _ensure_can_access_patient(current_user, patient_id)
    results = _health_memory.search_history(db, patient_id, query)

    if not results:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    return results


# ==================== VISITS ====================

@router.post("/{patient_id}/visits", response_model=VisitResponse)
async def create_visit(
    patient_id: str,
    visit: VisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new visit record.

    Args:
        patient_id: Patient identifier
        visit: Visit data

    Returns:
        Created visit record
    """
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to create visit records")
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List patient visits (most recent first).

    Args:
        patient_id: Patient identifier
        limit: Maximum number of visits to return

    Returns:
        List of visits
    """
    _ensure_can_access_patient(current_user, patient_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new prescription record.

    Args:
        patient_id: Patient identifier
        prescription: Prescription data

    Returns:
        Created prescription record
    """
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to create prescriptions")
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List patient prescriptions.

    Args:
        patient_id: Patient identifier
        status: Optional status filter

    Returns:
        List of prescriptions
    """
    _ensure_can_access_patient(current_user, patient_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to update prescriptions")
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new diagnosis record.

    Args:
        patient_id: Patient identifier
        diagnosis: Diagnosis data

    Returns:
        Created diagnosis record
    """
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized to create diagnoses")
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List patient diagnoses.

    Args:
        patient_id: Patient identifier
        status: Optional status filter

    Returns:
        List of diagnoses
    """
    _ensure_can_access_patient(current_user, patient_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    # Doctors/admins for any patient; a patient may only add to their own record.
    _ensure_can_access_patient(current_user, patient_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List patient allergies.

    CRITICAL for drug interaction checking.

    Args:
        patient_id: Patient identifier

    Returns:
        List of allergies
    """
    _ensure_can_access_patient(current_user, patient_id)
    allergies = _health_memory.get_allergies(db, patient_id)

    if allergies is None:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    return allergies


# ==================== HEALTH CHECK-INS ====================


@router.get("/{patient_id}/health-history")
async def get_health_history(
    patient_id: str,
    limit: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return last N daily check-ins for a patient (user_id = patient_id)."""
    _ensure_can_access_patient(current_user, patient_id)
    rows = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == patient_id)
        .order_by(CheckIn.date.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "patientId": r.user_id,
            "mood": r.mood,
            "energy": r.energy_level,
            "sleep": r.sleep_hours,
            "symptoms": r.symptoms or [],
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "date": r.date.isoformat() if r.date else None,
        }
        for r in rows
    ]


@router.post("/{patient_id}/check-in", status_code=201)
async def submit_check_in(
    patient_id: str,
    payload: CheckInCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a daily check-in for a patient. Upserts on today's date."""
    _ensure_can_access_patient(current_user, patient_id)
    today = date_type.today()
    existing = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == patient_id, CheckIn.date == today)
        .first()
    )
    if existing:
        row = existing
    else:
        row = CheckIn(user_id=patient_id, date=today)
        db.add(row)

    row.mood = payload.mood
    row.energy_level = payload.energy
    row.sleep_hours = payload.sleep
    row.symptoms = payload.symptoms
    row.pain_level = payload.painLevel

    db.commit()
    db.refresh(row)
    return {
        "id": str(row.id),
        "patientId": row.user_id,
        "mood": row.mood,
        "energy": row.energy_level,
        "sleep": row.sleep_hours,
        "symptoms": row.symptoms or [],
        "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        "date": row.date.isoformat() if row.date else None,
    }
