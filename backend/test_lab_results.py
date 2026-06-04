"""
Lab Results agent + API tests (Task 15).

Two layers:

1. Pure agent logic (no DB / HTTP) — fast, deterministic assertions on the
   rule-based interpreter: HbA1c bands, the critical-potassium flag, and the
   multi-result diabetes pattern.
2. HTTP contract — POST /api/lab-results/interpret returns 200 with the expected
   shape; save + ownership: a patient may only read their OWN saved sets, a
   doctor may read any patient's sets.

Uses an isolated in-memory SQLite database and overrides get_db; the app lifespan
is deliberately NOT executed (it would seed the real database).
"""

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import Base, get_db  # noqa: E402
from models.user import User  # noqa: E402
from main import app  # noqa: E402
from services.auth_service import hash_password, create_access_token  # noqa: E402
from agents.lab_results_agent import LabResultsAgent  # noqa: E402

# Importing the router module registers its LabResultSet table on Base.metadata.
import routers.lab_results as lab_results_router  # noqa: E402,F401


# ---------------------------------------------------------------------------
# Pure agent tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def agent():
    return LabResultsAgent()


def test_normal_hba1c_is_normal(agent):
    assert agent.get_result_status("hba1c", 5.0) == "normal"


def test_diabetic_hba1c_is_high(agent):
    assert agent.get_result_status("hba1c", 7.5) == "high"

    interp = agent.interpret_results([{"test_name": "hba1c", "value": 7.5, "unit": "%"}])
    row = interp["results"][0]
    assert row["status"] == "high"
    assert row["action_needed"] is True
    # Explanation should mention the diabetes range, not claim a diagnosis.
    assert "diabetes" in row["explanation"].lower()
    assert interp["disclaimer"]
    assert interp["stub_mode"] is False


def test_prediabetic_hba1c_is_high_band(agent):
    # 6.0% falls in the prediabetes band → still flagged "high" vs the normal range.
    assert agent.get_result_status("hba1c", 6.0) == "high"


def test_critical_potassium_flag(agent):
    # 6.8 mEq/L exceeds the 6.5 critical-high threshold.
    assert agent.get_result_status("potassium", 6.8) == "critical"

    interp = agent.interpret_results([{"test_name": "potassium", "value": 6.8, "unit": "mEq/L"}])
    assert interp["critical_flags"], "expected at least one critical flag"
    joined = " ".join(interp["critical_flags"]).lower()
    assert "potassium" in joined
    assert "immediate" in joined


def test_normal_potassium_has_no_critical_flag(agent):
    interp = agent.interpret_results([{"test_name": "potassium", "value": 4.2, "unit": "mEq/L"}])
    assert interp["critical_flags"] == []
    assert interp["results"][0]["status"] == "normal"


def test_diabetes_pattern_detection(agent):
    """High fasting glucose + high HbA1c together → a diabetes-risk pattern."""
    results = [
        {"test_name": "fasting_glucose", "value": 180, "unit": "mg/dL"},
        {"test_name": "hba1c", "value": 8.2, "unit": "%"},
    ]
    patterns = agent.detect_patterns(results)
    assert patterns, "expected at least one detected pattern"
    text = " ".join(patterns).lower()
    assert "glucose" in text and "hba1c" in text


def test_alias_resolution_for_a1c(agent):
    """The 'a1c' alias maps to hba1c and classifies the same."""
    assert agent.get_result_status("a1c", 7.5) == "high"


# ---------------------------------------------------------------------------
# HTTP / DB fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    test_client = TestClient(app)  # no lifespan (see module docstring)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


def _make_user(db_session, role="patient", email=None):
    user = User(
        email=email or f"{role}.{uuid.uuid4().hex[:8]}@swasthya.local",
        hashed_password=hash_password("Patient@1234"),
        full_name=f"Test {role.title()}",
        role=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth(user):
    token = create_access_token({"sub": user.id, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# HTTP: interpret
# ---------------------------------------------------------------------------

def test_interpret_endpoint_requires_auth(client):
    resp = client.post(
        "/api/lab-results/interpret",
        json={"results": [{"test_name": "hba1c", "value": 5.0}]},
    )
    assert resp.status_code == 401


def test_interpret_endpoint_returns_200_with_interpretation(client, db_session):
    user = _make_user(db_session)
    resp = client.post(
        "/api/lab-results/interpret",
        headers=_auth(user),
        json={
            "results": [
                {"test_name": "hba1c", "value": 7.5, "unit": "%"},
                {"test_name": "potassium", "value": 6.8, "unit": "mEq/L"},
            ],
            "patient_sex": "female",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["results"]) == 2
    assert body["disclaimer"]
    assert body["stub_mode"] is False
    # Potassium 6.8 must surface as a critical flag.
    assert body["critical_flags"], body
    statuses = {r["test_name"]: r["status"] for r in body["results"]}
    assert statuses["hba1c"] == "high"
    assert statuses["potassium"] == "critical"


def test_interpret_empty_results_is_422(client, db_session):
    user = _make_user(db_session)
    resp = client.post(
        "/api/lab-results/interpret",
        headers=_auth(user),
        json={"results": []},  # violates min_length=1
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# HTTP: save + ownership
# ---------------------------------------------------------------------------

def test_save_and_read_own_results(client, db_session):
    user = _make_user(db_session, email="owner@swasthya.local")
    save = client.post(
        "/api/lab-results/save",
        headers=_auth(user),
        json={
            "patient_id": user.id,
            "results": [{"test_name": "hba1c", "value": 5.4, "unit": "%"}],
            "lab_name": "City Lab",
        },
    )
    assert save.status_code == 201, save.text
    set_id = save.json()["id"]
    assert save.json()["saved"] is True

    read = client.get(f"/api/lab-results/{user.id}", headers=_auth(user))
    assert read.status_code == 200, read.text
    rows = read.json()
    assert any(r["id"] == set_id for r in rows)


def test_patient_cannot_read_another_patients_saved_results(client, db_session):
    owner = _make_user(db_session, email="patient.a@swasthya.local")
    other = _make_user(db_session, email="patient.b@swasthya.local")

    client.post(
        "/api/lab-results/save",
        headers=_auth(owner),
        json={
            "patient_id": owner.id,
            "results": [{"test_name": "hba1c", "value": 9.1, "unit": "%"}],
        },
    )

    # The other patient queries the owner's id — must NOT see the owner's set.
    resp = client.get(f"/api/lab-results/{owner.id}", headers=_auth(other))
    assert resp.status_code == 200
    assert resp.json() == [], "a patient must not read another patient's lab sets"


def test_doctor_can_read_any_patients_saved_results(client, db_session):
    patient = _make_user(db_session, email="pt@swasthya.local")
    doctor = _make_user(db_session, role="doctor", email="dr@swasthya.local")

    saved = client.post(
        "/api/lab-results/save",
        headers=_auth(patient),
        json={
            "patient_id": patient.id,
            "results": [{"test_name": "potassium", "value": 6.9, "unit": "mEq/L"}],
        },
    )
    assert saved.status_code == 201
    set_id = saved.json()["id"]

    resp = client.get(f"/api/lab-results/{patient.id}", headers=_auth(doctor))
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert any(r["id"] == set_id for r in rows)
    # The cached interpretation should retain the critical flag.
    target = next(r for r in rows if r["id"] == set_id)
    assert target["has_critical"] is True
    assert target["interpretation"]["critical_flags"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
