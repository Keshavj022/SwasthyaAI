"""
Health Memory Agent - Patient medical history retrieval and personalization.

Responsibilities:
- Retrieve patient profiles and demographics
- Access visit history and encounter data
- Query prescriptions (current and historical)
- Retrieve diagnoses and conditions
- Format longitudinal patient timelines
- Support personalized AI responses based on patient context

This agent provides READ-ONLY access to patient data for AI agents.
All WRITE operations go through the Patient Data API.
"""

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.patient import Patient, Visit, Prescription, Diagnosis, Allergy, LabResult


class HealthMemoryAgent(BaseAgent):
    """
    Retrieves and formats patient medical history for AI agents.
    """

    def __init__(self):
        super().__init__()
        self.name = "health_memory"

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Retrieve patient medical history based on query.

        Expected context keys:
        - patient_id: Patient identifier
        - query_type: "timeline", "prescriptions", "diagnoses", "summary"
        - time_range: Optional time range (e.g., "6 months", "1 year", "all")
        """
        # Extract patient ID from context
        patient_id = request.context.get("patient_id")

        if not patient_id:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                data={
                    "error": "patient_id required in context",
                    "usage": "Include patient_id in request context to retrieve medical history"
                },
                confidence=0.0,
                reasoning="No patient identifier provided",
                red_flags=[],
                requires_escalation=False
            )

        # This is a stub response since we don't have database session here
        # In production, database session would be passed through context
        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "message": f"Health Memory Agent ready to retrieve history for patient {patient_id}",
                "note": "This agent requires database session to retrieve actual patient data",
                "available_queries": [
                    "Get patient timeline",
                    "List active prescriptions",
                    "Review past diagnoses",
                    "Check allergies",
                    "View recent lab results"
                ]
            },
            confidence=1.0,
            reasoning="Health memory agent information",
            red_flags=[],
            requires_escalation=False
        )

    def get_patient_summary(self, db: Session, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive patient summary with all key information.

        Args:
            db: Database session
            patient_id: Patient identifier

        Returns:
            Dict with patient summary or None if not found
        """
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()

        if not patient:
            return None

        # Get active prescriptions
        active_prescriptions = db.query(Prescription).filter(
            Prescription.patient_id == patient.id,
            Prescription.status == "active"
        ).all()

        # Get active diagnoses
        active_diagnoses = db.query(Diagnosis).filter(
            Diagnosis.patient_id == patient.id,
            Diagnosis.status.in_(["active", "chronic"])
        ).all()

        # Get allergies
        allergies = db.query(Allergy).filter(
            Allergy.patient_id == patient.id,
            Allergy.status == "active"
        ).all()

        # Get recent visits (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        recent_visits = db.query(Visit).filter(
            Visit.patient_id == patient.id,
            Visit.visit_date >= six_months_ago
        ).order_by(Visit.visit_date.desc()).limit(5).all()

        return {
            "patient_info": {
                "patient_id": patient.patient_id,
                "name": f"{patient.first_name} {patient.last_name}",
                "age": self._calculate_age(patient.date_of_birth),
                "gender": patient.gender,
                "blood_type": patient.blood_type
            },
            "active_prescriptions": [
                {
                    "medication": rx.medication_name,
                    "dosage": rx.dosage,
                    "frequency": rx.frequency,
                    "prescribed_date": rx.prescribed_date.isoformat()
                }
                for rx in active_prescriptions
            ],
            "active_diagnoses": [
                {
                    "diagnosis": diag.diagnosis_name,
                    "icd10": diag.icd10_code,
                    "status": diag.status,
                    "diagnosed_date": diag.diagnosis_date.isoformat()
                }
                for diag in active_diagnoses
            ],
            "allergies": [
                {
                    "allergen": allergy.allergen,
                    "type": allergy.allergen_type,
                    "reaction": allergy.reaction,
                    "severity": allergy.severity
                }
                for allergy in allergies
            ],
            "recent_visits": [
                {
                    "date": visit.visit_date.isoformat(),
                    "type": visit.visit_type,
                    "chief_complaint": visit.chief_complaint,
                    "provider": visit.provider_name
                }
                for visit in recent_visits
            ]
        }

    def get_patient_timeline(
        self,
        db: Session,
        patient_id: str,
        months: int = 12
    ) -> Optional[Dict[str, Any]]:
        """
        Get chronological timeline of all patient events.

        Args:
            db: Database session
            patient_id: Patient identifier
            months: Number of months to include (default: 12)

        Returns:
            Dict with timeline events or None if patient not found
        """
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()

        if not patient:
            return None

        since_date = datetime.utcnow() - timedelta(days=months * 30)

        # Collect all events
        events = []

        # Visits
        visits = db.query(Visit).filter(
            Visit.patient_id == patient.id,
            Visit.visit_date >= since_date
        ).all()

        for visit in visits:
            events.append({
                "date": visit.visit_date.isoformat(),
                "type": "visit",
                "description": f"{visit.visit_type.title()} visit: {visit.chief_complaint}",
                "details": {
                    "provider": visit.provider_name,
                    "assessment": visit.assessment
                }
            })

        # Prescriptions started
        prescriptions = db.query(Prescription).filter(
            Prescription.patient_id == patient.id,
            Prescription.prescribed_date >= since_date.date()
        ).all()

        for rx in prescriptions:
            events.append({
                "date": rx.prescribed_date.isoformat(),
                "type": "prescription",
                "description": f"Started {rx.medication_name} ({rx.dosage})",
                "details": {
                    "frequency": rx.frequency,
                    "indication": rx.indication,
                    "status": rx.status
                }
            })

        # Diagnoses
        diagnoses = db.query(Diagnosis).filter(
            Diagnosis.patient_id == patient.id,
            Diagnosis.diagnosis_date >= since_date.date()
        ).all()

        for diag in diagnoses:
            events.append({
                "date": diag.diagnosis_date.isoformat(),
                "type": "diagnosis",
                "description": f"Diagnosed with {diag.diagnosis_name}",
                "details": {
                    "icd10": diag.icd10_code,
                    "severity": diag.severity,
                    "status": diag.status
                }
            })

        # Lab results
        labs = db.query(LabResult).filter(
            LabResult.patient_id == patient.id,
            LabResult.test_date >= since_date
        ).all()

        for lab in labs:
            events.append({
                "date": lab.test_date.isoformat(),
                "type": "lab_result",
                "description": f"{lab.test_name}: {lab.result_value} {lab.result_unit}",
                "details": {
                    "reference_range": lab.reference_range,
                    "flag": lab.flag
                }
            })

        # Sort by date (most recent first)
        events.sort(key=lambda x: x["date"], reverse=True)

        return {
            "patient_id": patient.patient_id,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "timeline_period": f"Last {months} months",
            "total_events": len(events),
            "events": events
        }

    def get_active_medications(self, db: Session, patient_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of currently active medications.

        Args:
            db: Database session
            patient_id: Patient identifier

        Returns:
            List of active medications or None if patient not found
        """
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()

        if not patient:
            return None

        prescriptions = db.query(Prescription).filter(
            Prescription.patient_id == patient.id,
            Prescription.status == "active"
        ).order_by(Prescription.prescribed_date.desc()).all()

        return [
            {
                "medication_name": rx.medication_name,
                "generic_name": rx.generic_name,
                "dosage": rx.dosage,
                "route": rx.route,
                "frequency": rx.frequency,
                "instructions": rx.instructions,
                "prescribed_date": rx.prescribed_date.isoformat(),
                "prescriber": rx.prescriber_name,
                "indication": rx.indication
            }
            for rx in prescriptions
        ]

    def get_allergies(self, db: Session, patient_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of patient allergies (critical for drug safety).

        Args:
            db: Database session
            patient_id: Patient identifier

        Returns:
            List of allergies or None if patient not found
        """
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()

        if not patient:
            return None

        allergies = db.query(Allergy).filter(
            Allergy.patient_id == patient.id,
            Allergy.status == "active"
        ).all()

        return [
            {
                "allergen": allergy.allergen,
                "allergen_type": allergy.allergen_type,
                "reaction": allergy.reaction,
                "severity": allergy.severity,
                "onset_date": allergy.onset_date.isoformat() if allergy.onset_date else None
            }
            for allergy in allergies
        ]

    def get_chronic_conditions(self, db: Session, patient_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of chronic conditions/diagnoses.

        Args:
            db: Database session
            patient_id: Patient identifier

        Returns:
            List of chronic conditions or None if patient not found
        """
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()

        if not patient:
            return None

        diagnoses = db.query(Diagnosis).filter(
            Diagnosis.patient_id == patient.id,
            Diagnosis.status.in_(["chronic", "active"])
        ).order_by(Diagnosis.diagnosis_date.desc()).all()

        return [
            {
                "diagnosis": diag.diagnosis_name,
                "icd10_code": diag.icd10_code,
                "diagnosed_date": diag.diagnosis_date.isoformat(),
                "status": diag.status,
                "severity": diag.severity,
                "notes": diag.clinical_notes
            }
            for diag in diagnoses
        ]

    def search_history(
        self,
        db: Session,
        patient_id: str,
        search_term: str
    ) -> Optional[Dict[str, Any]]:
        """
        Search patient history for specific term.

        Args:
            db: Database session
            patient_id: Patient identifier
            search_term: Term to search for

        Returns:
            Dict with search results or None if patient not found
        """
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()

        if not patient:
            return None

        search_lower = search_term.lower()
        results = {
            "search_term": search_term,
            "visits": [],
            "prescriptions": [],
            "diagnoses": [],
            "labs": []
        }

        # Search visits
        visits = db.query(Visit).filter(Visit.patient_id == patient.id).all()
        for visit in visits:
            if (search_lower in (visit.chief_complaint or "").lower() or
                search_lower in (visit.assessment or "").lower()):
                results["visits"].append({
                    "date": visit.visit_date.isoformat(),
                    "type": visit.visit_type,
                    "chief_complaint": visit.chief_complaint
                })

        # Search prescriptions
        prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient.id).all()
        for rx in prescriptions:
            if search_lower in rx.medication_name.lower():
                results["prescriptions"].append({
                    "medication": rx.medication_name,
                    "dosage": rx.dosage,
                    "prescribed_date": rx.prescribed_date.isoformat(),
                    "status": rx.status
                })

        # Search diagnoses
        diagnoses = db.query(Diagnosis).filter(Diagnosis.patient_id == patient.id).all()
        for diag in diagnoses:
            if search_lower in diag.diagnosis_name.lower():
                results["diagnoses"].append({
                    "diagnosis": diag.diagnosis_name,
                    "diagnosed_date": diag.diagnosis_date.isoformat(),
                    "status": diag.status
                })

        # Search lab results
        labs = db.query(LabResult).filter(LabResult.patient_id == patient.id).all()
        for lab in labs:
            if search_lower in lab.test_name.lower():
                results["labs"].append({
                    "test": lab.test_name,
                    "result": f"{lab.result_value} {lab.result_unit}",
                    "date": lab.test_date.isoformat()
                })

        results["total_results"] = (
            len(results["visits"]) +
            len(results["prescriptions"]) +
            len(results["diagnoses"]) +
            len(results["labs"])
        )

        return results

    def _calculate_age(self, date_of_birth: datetime.date) -> int:
        """Calculate age from date of birth"""
        today = datetime.utcnow().date()
        return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )

    def get_capabilities(self) -> List[str]:
        return ["history", "past", "previous", "records", "timeline", "medical history"]

    def get_description(self) -> str:
        return "Retrieves patient medical history, prescriptions, diagnoses, and longitudinal data"

    def get_confidence_threshold(self) -> float:
        return 0.70
