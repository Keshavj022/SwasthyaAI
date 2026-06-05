"""
Seed Demo Data Script (Task 15).

Populates the local SQLite database with a coherent, demo-ready dataset that
matches the CURRENT SQLAlchemy models and the way the running app keys its data:

  * Users (admin / doctor / patient) are the primary identities. Patient-scoped
    data (check-ins, appointments, lab result sets) is keyed by the patient's
    ``User.id`` — exactly as the live API does.
  * A clinical ``Patient`` profile row (plus a few diagnoses / prescriptions /
    allergies / lab results) is created per demo patient, keyed by
    ``patient_id == user.id`` so the patient-records pages resolve.

Demo accounts (all under @swasthya.local):
  admin@swasthya.local        / Admin@1234    (admin)
  dr.sharma@swasthya.local    / Doctor@1234   (doctor, Cardiologist)
  dr.mehta@swasthya.local     / Doctor@1234   (doctor, Neurologist)
  patient.rahul@swasthya.local/ Patient@1234  (patient, 35yo male)
  patient.priya@swasthya.local/ Patient@1234  (patient, 28yo female)

The script is IDEMPOTENT: re-running it will not create duplicates. Existing rows
are matched by a stable natural key (email / user-day check-in / etc.) and reused.

Usage:
    cd backend
    python seed_demo_data.py
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Make the backend package importable when run from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import SessionLocal, init_db  # noqa: E402
from models.user import User  # noqa: E402
from models.patient import (  # noqa: E402
    Patient,
    Diagnosis,
    Prescription,
    Allergy,
    LabResult,
)
from models.health_monitoring import CheckIn  # noqa: E402
from models.appointment import Appointment  # noqa: E402
from models.system import AuditLog  # noqa: E402
from services.auth_service import hash_password  # noqa: E402

# Importing the router registers the LabResultSet table on Base.metadata and
# gives us the deterministic interpreter used by the live /interpret endpoint.
from routers.lab_results import LabResultSet  # noqa: E402
from agents.lab_results_agent import LabResultsAgent  # noqa: E402

_lab_agent = LabResultsAgent()


# ---------------------------------------------------------------------------
# Demo definitions
# ---------------------------------------------------------------------------

DEMO_USERS = [
    {
        "email": "admin@swasthya.local",
        "password": "Admin@1234",
        "full_name": "System Administrator",
        "role": "admin",
    },
    {
        "email": "dr.sharma@swasthya.local",
        "password": "Doctor@1234",
        "full_name": "Dr. Priya Sharma",
        "role": "doctor",
        "specialty": "Cardiology",
        "license_number": "MCI-CARD-10293",
    },
    {
        "email": "dr.mehta@swasthya.local",
        "password": "Doctor@1234",
        "full_name": "Dr. Rahul Mehta",
        "role": "doctor",
        "specialty": "Neurology",
        "license_number": "MCI-NEUR-44871",
    },
    {
        "email": "patient.rahul@swasthya.local",
        "password": "Patient@1234",
        "full_name": "Rahul Verma",
        "role": "patient",
        "date_of_birth": date(1990, 8, 12),  # ~35yo
        "blood_group": "B+",
    },
    {
        "email": "patient.priya@swasthya.local",
        "password": "Patient@1234",
        "full_name": "Priya Nair",
        "role": "patient",
        "date_of_birth": date(1997, 3, 4),  # ~28yo
        "blood_group": "O+",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_user(db, spec: dict) -> User:
    """Idempotently create a User keyed by email; keep its existing id on re-run."""
    user = db.query(User).filter(User.email == spec["email"]).first()
    if user:
        return user
    user = User(
        email=spec["email"],
        hashed_password=hash_password(spec["password"]),
        full_name=spec["full_name"],
        role=spec["role"],
        is_active=True,
        date_of_birth=spec.get("date_of_birth"),
        blood_group=spec.get("blood_group"),
        specialty=spec.get("specialty"),
        license_number=spec.get("license_number"),
    )
    db.add(user)
    db.flush()  # assign the uuid id without a full commit yet
    return user


def _ensure_patient_profile(db, user: User, gender: str) -> Patient:
    """Create a clinical Patient profile keyed by patient_id == user.id."""
    existing = db.query(Patient).filter(Patient.patient_id == user.id).first()
    if existing:
        return existing
    first, _, last = user.full_name.partition(" ")
    patient = Patient(
        patient_id=user.id,
        mrn=f"MRN-{user.id[:8]}",
        first_name=first or user.full_name,
        last_name=last or "",
        date_of_birth=user.date_of_birth or date(1990, 1, 1),
        gender=gender,
        email=user.email,
        blood_type=user.blood_group,
        active=True,
    )
    db.add(patient)
    db.flush()
    return patient


def _seed_checkins(db, user: User, profile_seed: int) -> int:
    """14 days of daily check-ins for a patient (keyed by user.id). Idempotent."""
    created = 0
    today = date.today()
    for offset in range(14):
        d = today - timedelta(days=offset)
        exists = (
            db.query(CheckIn)
            .filter(CheckIn.user_id == user.id, CheckIn.date == d)
            .first()
        )
        if exists:
            continue
        # Deterministic but varied values so trend charts look natural.
        wobble = (offset + profile_seed) % 5
        db.add(
            CheckIn(
                user_id=user.id,
                date=d,
                time="08:30",
                mood=5 + (wobble % 4),
                energy_level=4 + ((offset + profile_seed) % 5),
                sleep_hours=6.0 + (wobble * 0.4),
                pain_level=max(0, 3 - (offset % 4)),
                symptoms=(["headache"] if offset % 4 == 0 else
                          ["fatigue"] if offset % 4 == 1 else []),
            )
        )
        created += 1
    return created


def _seed_lab_sets(db, user: User, normal_set: list, flagged_set: list,
                   lab_name: str) -> int:
    """Two lab result sets per patient: one normal, one with flags. Idempotent."""
    created = 0
    sets = [
        (normal_set, "Routine wellness panel", date.today() - timedelta(days=20)),
        (flagged_set, "Follow-up metabolic panel", date.today() - timedelta(days=3)),
    ]
    for results, label, report_date in sets:
        # Idempotency key: owner + report_date + lab label.
        exists = (
            db.query(LabResultSet)
            .filter(
                LabResultSet.owner_user_id == user.id,
                LabResultSet.report_date == report_date,
                LabResultSet.lab_name == lab_name,
            )
            .first()
        )
        if exists:
            continue
        interpretation = _lab_agent.interpret_results(results, None, None)
        raw = [{"test_name": r["test_name"], "value": r["value"], "unit": r.get("unit")}
               for r in results]
        db.add(
            LabResultSet(
                owner_user_id=user.id,
                patient_id=user.id,
                lab_name=lab_name,
                report_date=report_date,
                results=raw,
                interpretation=interpretation,
                test_count=len(raw),
                has_critical=bool(interpretation.get("critical_flags")),
            )
        )
        created += 1
    return created


def _seed_clinical_records(db, patient: Patient, payload: dict) -> None:
    """A couple of diagnoses / prescriptions / allergies / lab rows. Idempotent."""
    for dx in payload.get("diagnoses", []):
        exists = (
            db.query(Diagnosis)
            .filter(
                Diagnosis.patient_id == patient.id,
                Diagnosis.diagnosis_name == dx["diagnosis_name"],
            )
            .first()
        )
        if not exists:
            db.add(Diagnosis(patient_id=patient.id, **dx))

    for rx in payload.get("prescriptions", []):
        exists = (
            db.query(Prescription)
            .filter(
                Prescription.patient_id == patient.id,
                Prescription.medication_name == rx["medication_name"],
            )
            .first()
        )
        if not exists:
            db.add(Prescription(patient_id=patient.id, **rx))

    for al in payload.get("allergies", []):
        exists = (
            db.query(Allergy)
            .filter(
                Allergy.patient_id == patient.id,
                Allergy.allergen == al["allergen"],
            )
            .first()
        )
        if not exists:
            db.add(Allergy(patient_id=patient.id, **al))

    for lab in payload.get("lab_results", []):
        exists = (
            db.query(LabResult)
            .filter(
                LabResult.patient_id == patient.id,
                LabResult.test_name == lab["test_name"],
                LabResult.test_date == lab["test_date"],
            )
            .first()
        )
        if not exists:
            db.add(LabResult(patient_id=patient.id, **lab))


def _next_weekday_at(days_ahead: int, hour: int, minute: int = 0) -> datetime:
    """A datetime `days_ahead` from now, nudged off Sunday (clinic closed)."""
    target = (datetime.now() + timedelta(days=days_ahead)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    if target.weekday() == 6:  # Sunday → push to Monday
        target += timedelta(days=1)
    return target


def _seed_appointments(db, patients: dict, doctors: dict) -> int:
    """5 upcoming + 3 past appointments. Idempotent on (patient, doctor, time)."""
    rahul = patients["patient.rahul@swasthya.local"]
    priya = patients["patient.priya@swasthya.local"]
    sharma = doctors["dr.sharma@swasthya.local"]
    mehta = doctors["dr.mehta@swasthya.local"]

    specs = [
        # Upcoming
        (rahul, sharma, _next_weekday_at(2, 10, 0), 30, "scheduled",
         "consultation", "Chest tightness on exertion — cardiology review"),
        (rahul, mehta, _next_weekday_at(6, 14, 30), 45, "scheduled",
         "follow_up", "Recurrent migraines follow-up"),
        (priya, sharma, _next_weekday_at(3, 9, 30), 30, "scheduled",
         "consultation", "Palpitations evaluation"),
        (priya, mehta, _next_weekday_at(9, 11, 0), 30, "confirmed",
         "consultation", "Tension headaches assessment"),
        (rahul, sharma, _next_weekday_at(13, 15, 0), 30, "scheduled",
         "follow_up", "Blood-pressure recheck"),
        # Past
        (rahul, sharma, _next_weekday_at(-21, 10, 0), 30, "completed",
         "consultation", "Annual cardiac screening"),
        (priya, mehta, _next_weekday_at(-14, 13, 0), 45, "completed",
         "consultation", "Initial neurology consult"),
        (priya, sharma, _next_weekday_at(-7, 9, 0), 30, "cancelled",
         "consultation", "Rescheduled by patient"),
    ]

    created = 0
    for patient, doctor, dt, dur, status, atype, reason in specs:
        exists = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id == patient.id,
                Appointment.doctor_id == doctor.id,
                Appointment.date_time == dt,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            Appointment(
                patient_id=patient.id,
                patient_name=patient.full_name,
                doctor_id=doctor.id,
                doctor_name=doctor.full_name,
                specialty=doctor.specialty,
                date_time=dt,
                duration_minutes=dur,
                status=status,
                type=atype,
                reason=reason,
            )
        )
        created += 1
    return created


def _seed_audit_logs(db, patients: dict) -> int:
    """~20 AI-interaction audit logs spread across recent days. Idempotent-ish.

    We only seed if the audit table is (near) empty for our demo users so a
    re-run does not keep appending. user_id is stored hashed, matching the
    audit logger's privacy model.
    """
    import hashlib

    def _h(uid: str) -> str:
        return hashlib.sha256(uid.encode()).hexdigest()[:16]

    rahul = patients["patient.rahul@swasthya.local"]
    priya = patients["patient.priya@swasthya.local"]
    hashed_ids = {_h(rahul.id), _h(priya.id)}

    already = (
        db.query(AuditLog)
        .filter(AuditLog.user_id.in_(hashed_ids))
        .count()
    )
    if already >= 20:
        return 0

    samples = [
        ("triage", "I have a mild headache and slight fever", 72, None),
        ("triage", "Sudden severe chest pain radiating to left arm", 88, "cardiac"),
        ("diagnostic_support", "Persistent cough for two weeks", 64, None),
        ("drug_info", "Can I take ibuprofen with my blood pressure medicine?", 81, None),
        ("lab_results", "Interpret my HbA1c result of 7.5%", 82, None),
        ("communication", "What does hypertension mean in simple terms?", 90, None),
        ("health_support", "Help me track my daily mood and energy", 77, None),
        ("appointment", "Book a cardiology appointment next week", 85, None),
        ("triage", "I feel dizzy when I stand up quickly", 69, None),
        ("diagnostic_support", "Lower back pain after lifting weights", 66, None),
    ]

    base = datetime.utcnow()
    created = 0
    for i in range(20):
        agent, message, score, escalation = samples[i % len(samples)]
        actor = rahul if i % 2 == 0 else priya
        db.add(
            AuditLog(
                timestamp=base - timedelta(hours=i * 5),
                user_id=_h(actor.id),
                agent_name=agent,
                action="agent_query",
                input_data={"message": message},
                output_data={"agent": agent, "disclaimer_applied": "⚠️ Decision support only"},
                confidence_score=score,
                reasoning_summary=f"Routed to {agent} based on message keywords.",
                escalation_triggered=escalation,
                safety_flags={"red_flag": escalation} if escalation else None,
            )
        )
        created += 1
    return created


# ---------------------------------------------------------------------------
# Patient clinical payloads
# ---------------------------------------------------------------------------

RAHUL_CLINICAL = {
    "diagnoses": [
        {"diagnosis_name": "Essential hypertension", "icd10_code": "I10",
         "diagnosis_type": "chronic", "severity": "moderate", "status": "active",
         "diagnosis_date": date(2022, 6, 1), "diagnosed_by": "Dr. Priya Sharma"},
    ],
    "prescriptions": [
        {"medication_name": "Amlodipine", "dosage": "5mg", "route": "oral",
         "frequency": "once daily", "status": "active",
         "prescribed_date": date(2022, 6, 1), "indication": "Hypertension",
         "prescriber_name": "Dr. Priya Sharma"},
    ],
    "allergies": [
        {"allergen": "Penicillin", "allergen_type": "drug",
         "reaction": "Rash and hives", "severity": "moderate", "status": "active"},
    ],
    "lab_results": [
        {"test_name": "HbA1c", "category": "chemistry", "result_value": "7.5",
         "result_unit": "%", "reference_range": "<5.7", "flag": "high",
         "test_date": datetime(2025, 12, 1, 9, 0)},
    ],
}

PRIYA_CLINICAL = {
    "diagnoses": [
        {"diagnosis_name": "Migraine without aura", "icd10_code": "G43.0",
         "diagnosis_type": "chronic", "severity": "mild", "status": "active",
         "diagnosis_date": date(2023, 2, 15), "diagnosed_by": "Dr. Rahul Mehta"},
    ],
    "prescriptions": [
        {"medication_name": "Sumatriptan", "dosage": "50mg", "route": "oral",
         "frequency": "as needed", "status": "active",
         "prescribed_date": date(2023, 2, 15), "indication": "Acute migraine",
         "prescriber_name": "Dr. Rahul Mehta"},
    ],
    "allergies": [
        {"allergen": "Latex", "allergen_type": "environmental",
         "reaction": "Contact dermatitis", "severity": "mild", "status": "active"},
    ],
    "lab_results": [
        {"test_name": "Hemoglobin", "category": "hematology", "result_value": "11.2",
         "result_unit": "g/dL", "reference_range": "12.0-15.5", "flag": "low",
         "test_date": datetime(2025, 12, 2, 9, 0)},
    ],
}

# Lab sets fed through the live interpreter (one normal, one flagged).
RAHUL_LAB_NORMAL = [
    {"test_name": "hba1c", "value": 5.3, "unit": "%"},
    {"test_name": "total_cholesterol", "value": 180, "unit": "mg/dL"},
    {"test_name": "potassium", "value": 4.2, "unit": "mEq/L"},
]
RAHUL_LAB_FLAGGED = [
    {"test_name": "hba1c", "value": 7.5, "unit": "%"},
    {"test_name": "fasting_glucose", "value": 165, "unit": "mg/dL"},
    {"test_name": "ldl", "value": 172, "unit": "mg/dL"},
]
PRIYA_LAB_NORMAL = [
    {"test_name": "hemoglobin", "value": 13.4, "unit": "g/dL"},
    {"test_name": "tsh", "value": 2.1, "unit": "mIU/L"},
]
PRIYA_LAB_FLAGGED = [
    {"test_name": "hemoglobin", "value": 10.8, "unit": "g/dL"},
    {"test_name": "potassium", "value": 6.8, "unit": "mEq/L"},  # critical
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def seed() -> dict:
    """Run the full idempotent seed and return a summary of counts."""
    init_db()  # ensure every table (incl. lab_result_sets) exists

    db = SessionLocal()
    summary = {
        "users": 0, "patients": 0, "checkins": 0,
        "lab_sets": 0, "appointments": 0, "audit_logs": 0,
    }
    try:
        # 1) Users
        users_by_email: dict[str, User] = {}
        for spec in DEMO_USERS:
            existed = db.query(User).filter(User.email == spec["email"]).first()
            user = _get_or_create_user(db, spec)
            users_by_email[spec["email"]] = user
            if not existed:
                summary["users"] += 1
        db.flush()

        patients = {
            e: u for e, u in users_by_email.items() if u.role == "patient"
        }
        doctors = {
            e: u for e, u in users_by_email.items() if u.role == "doctor"
        }

        # 2) Patient clinical profiles + records
        genders = {
            "patient.rahul@swasthya.local": "male",
            "patient.priya@swasthya.local": "female",
        }
        clinical = {
            "patient.rahul@swasthya.local": RAHUL_CLINICAL,
            "patient.priya@swasthya.local": PRIYA_CLINICAL,
        }
        for email, user in patients.items():
            existed = db.query(Patient).filter(Patient.patient_id == user.id).first()
            profile = _ensure_patient_profile(db, user, genders[email])
            if not existed:
                summary["patients"] += 1
            _seed_clinical_records(db, profile, clinical[email])

        # 3) Check-ins (14 days each)
        for seed_idx, (email, user) in enumerate(patients.items()):
            summary["checkins"] += _seed_checkins(db, user, profile_seed=seed_idx)

        # 4) Lab result sets (normal + flagged each)
        summary["lab_sets"] += _seed_lab_sets(
            db, patients["patient.rahul@swasthya.local"],
            RAHUL_LAB_NORMAL, RAHUL_LAB_FLAGGED, lab_name="Apollo Diagnostics",
        )
        summary["lab_sets"] += _seed_lab_sets(
            db, patients["patient.priya@swasthya.local"],
            PRIYA_LAB_NORMAL, PRIYA_LAB_FLAGGED, lab_name="Metropolis Labs",
        )

        # 5) Appointments
        summary["appointments"] += _seed_appointments(db, patients, doctors)

        # 6) Audit logs
        summary["audit_logs"] += _seed_audit_logs(db, patients)

        db.commit()
        return summary
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    print("=" * 70)
    print("SwasthyaAI — DEMO DATA SEEDER")
    print("=" * 70)
    try:
        summary = seed()
    except Exception as exc:  # pragma: no cover - operator feedback
        print(f"\n❌ Error seeding data: {type(exc).__name__}: {exc}")
        print("\nMake sure you are running from the backend/ directory.")
        return 1

    print("\nSeed complete (idempotent — re-runs add only what is missing):")
    print(f"  Users created this run ........ {summary['users']}")
    print(f"  Patient profiles created ...... {summary['patients']}")
    print(f"  Check-ins created ............. {summary['checkins']}")
    print(f"  Lab result sets created ....... {summary['lab_sets']}")
    print(f"  Appointments created .......... {summary['appointments']}")
    print(f"  Audit logs created ............ {summary['audit_logs']}")
    print("\nDemo accounts:")
    print("  admin@swasthya.local         / Admin@1234")
    print("  dr.sharma@swasthya.local     / Doctor@1234   (Cardiology)")
    print("  dr.mehta@swasthya.local      / Doctor@1234   (Neurology)")
    print("  patient.rahul@swasthya.local / Patient@1234")
    print("  patient.priya@swasthya.local / Patient@1234")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
