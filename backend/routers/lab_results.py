from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import get_current_user
from schemas.lab_results import (
    InterpretRequest, LabResultsResponse,
    SaveLabReportRequest, SavedLabReport,
    LabResultInput,
)
from agents.lab_results_agent import LabResultsAgent
from models.lab_results import SavedLabResult
from datetime import datetime
import uuid

router = APIRouter(prefix="/lab-results", tags=["lab-results"])
agent = LabResultsAgent()


@router.post("/interpret", response_model=LabResultsResponse)
def interpret_lab_results(body: InterpretRequest, current_user=Depends(get_current_user)):
    return agent.interpret_results(body.results, body.patient_age, body.patient_sex)


@router.post("/save")
def save_lab_report(body: SaveLabReportRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if str(current_user.id) != body.patient_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to save results for this patient")
    # Interpret to check for critical flags
    interpreted = agent.interpret_results(body.results, body.patient_age, body.patient_sex)
    has_critical = len(interpreted.critical_flags) > 0

    report_id = str(uuid.uuid4())
    record = SavedLabResult(
        id=report_id,
        patient_id=body.patient_id,
        report_date=body.report_date,
        lab_name=body.lab_name,
        test_count=len(body.results),
        has_critical=has_critical,
        results_json=[r.model_dump() for r in body.results],
    )
    db.add(record)
    db.commit()
    return {"id": report_id, "saved": True}


@router.get("/{patient_id}", response_model=list[SavedLabReport])
def get_saved_reports(patient_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if str(current_user.id) != patient_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view results for this patient")
    records = (
        db.query(SavedLabResult)
        .filter(SavedLabResult.patient_id == patient_id)
        .order_by(SavedLabResult.created_at.desc())
        .all()
    )
    return [
        SavedLabReport(
            id=r.id,
            patient_id=r.patient_id,
            report_date=r.report_date,
            lab_name=r.lab_name,
            test_count=r.test_count,
            has_critical=r.has_critical,
            created_at=r.created_at.isoformat(),
            results=[LabResultInput(**item) for item in (r.results_json or [])],
        )
        for r in records
    ]
