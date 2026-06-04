"""
End-to-end API integration tests (Task 15).

Exercises the wired FastAPI app over HTTP with an isolated in-memory database:

- /api/orchestrator/query (and the /ask alias) require authentication.
- The orchestrator derives the actor from the JWT and IGNORES any client-supplied
  user_id (audit-trail spoofing protection), and writes an audit log.
- Cross-patient access is denied: a patient cannot read another patient's
  records via /api/patients/{id}/...; a doctor can.
- Public health surface: /api/health, /api/health/ping, /api/health/ai-status.

The orchestrator routes through the real agent registry, so we register all
agents once. The app lifespan is NOT executed (it would seed the real database);
instead get_db is overridden onto a throwaway session.
"""

import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import Base, get_db  # noqa: E402
from models.user import User  # noqa: E402
from models.system import AuditLog  # noqa: E402
from models.health_monitoring import CheckIn  # noqa: E402
from main import app  # noqa: E402
from services.auth_service import hash_password, create_access_token  # noqa: E402
from agents import register_all_agents  # noqa: E402
from orchestrator.audit_logger import audit_logger  # noqa: E402

# Register agents with the global registry exactly once for the whole module so
# the orchestrator can resolve an agent for each classified intent.
register_all_agents()


def _hashed_uid(user_id: str) -> str:
    """The audit trail stores a privacy hash of the user id, not the raw id."""
    return audit_logger._hash_user_id(str(user_id))


# ---------------------------------------------------------------------------
# Fixtures
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
# Health surface (public)
# ---------------------------------------------------------------------------

def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] in ("healthy", "degraded")
    assert body["database"]["status"] == "connected"


def test_health_ping(client):
    resp = client.get("/api/health/ping")
    assert resp.status_code == 200
    assert resp.json()["message"] == "pong"


def test_ai_status_endpoint(client):
    resp = client.get("/api/health/ai-status")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "models" in body
    assert "anyLoaded" in body
    assert isinstance(body["models"], list)
    # Models are disabled by default → all stubbed → nothing loaded.
    assert body["anyLoaded"] is False


# ---------------------------------------------------------------------------
# Orchestrator: auth + user_id derivation + audit
# ---------------------------------------------------------------------------

def test_orchestrator_query_requires_auth(client):
    resp = client.post("/api/orchestrator/query", json={"message": "I have a headache"})
    assert resp.status_code == 401


def test_orchestrator_ask_alias_requires_auth(client):
    resp = client.post("/api/orchestrator/ask", json={"message": "I have a headache"})
    assert resp.status_code == 401


def test_orchestrator_query_succeeds_and_writes_audit(client, db_session):
    user = _make_user(db_session)
    resp = client.post(
        "/api/orchestrator/query",
        headers=_auth(user),
        json={"message": "I have a mild headache and a runny nose"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["agent"]
    assert body["disclaimer"], "every AI response must carry a disclaimer"
    assert "data" in body

    # An audit log was created and is attributed to the authenticated user
    # (stored as a privacy hash of the user id, never the raw id).
    logs = db_session.query(AuditLog).all()
    assert len(logs) >= 1
    assert any(log.user_id == _hashed_uid(user.id) for log in logs)
    # The raw id must NOT be persisted in the clear.
    assert all(log.user_id != str(user.id) for log in logs)


def test_orchestrator_ignores_client_supplied_user_id(client, db_session):
    """A spoofed user_id in the body must NOT appear in the audit trail."""
    user = _make_user(db_session, email="real.actor@swasthya.local")
    spoofed = "victim-user-id-9999"

    resp = client.post(
        "/api/orchestrator/query",
        headers=_auth(user),
        json={"message": "I feel tired lately", "user_id": spoofed},
    )
    assert resp.status_code == 200, resp.text

    logs = db_session.query(AuditLog).all()
    assert logs, "expected an audit log entry"
    # Neither the raw spoofed id nor its hash may appear; the real actor's hash must.
    assert all(log.user_id != spoofed for log in logs)
    assert all(log.user_id != _hashed_uid(spoofed) for log in logs)
    assert any(log.user_id == _hashed_uid(user.id) for log in logs)


def test_orchestrator_empty_message_is_handled(client, db_session):
    """An empty message returns a graceful (non-crashing) response envelope."""
    user = _make_user(db_session)
    resp = client.post(
        "/api/orchestrator/query", headers=_auth(user), json={"message": ""}
    )
    assert resp.status_code == 200, resp.text
    assert "disclaimer" in resp.json()


# ---------------------------------------------------------------------------
# Cross-patient access control
# ---------------------------------------------------------------------------

def test_patient_can_read_own_health_history(client, db_session):
    patient = _make_user(db_session, email="self@swasthya.local")
    # Seed a couple of check-ins owned by this patient.
    for offset in range(2):
        db_session.add(
            CheckIn(
                user_id=patient.id,
                date=date.today() - timedelta(days=offset),
                mood=6,
                energy_level=7,
                sleep_hours=7.5,
                symptoms=[],
            )
        )
    db_session.commit()

    resp = client.get(
        f"/api/patients/{patient.id}/health-history", headers=_auth(patient)
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 2


def test_patient_cannot_read_other_patient_history(client, db_session):
    a = _make_user(db_session, email="a@swasthya.local")
    b = _make_user(db_session, email="b@swasthya.local")
    db_session.add(
        CheckIn(user_id=a.id, date=date.today(), mood=5, energy_level=5, symptoms=[])
    )
    db_session.commit()

    # b tries to read a's history → forbidden.
    resp = client.get(
        f"/api/patients/{a.id}/health-history", headers=_auth(b)
    )
    assert resp.status_code == 403


def test_doctor_can_read_any_patient_history(client, db_session):
    patient = _make_user(db_session, email="pt2@swasthya.local")
    doctor = _make_user(db_session, role="doctor", email="dr2@swasthya.local")
    db_session.add(
        CheckIn(user_id=patient.id, date=date.today(), mood=4, energy_level=4, symptoms=[])
    )
    db_session.commit()

    resp = client.get(
        f"/api/patients/{patient.id}/health-history", headers=_auth(doctor)
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 1


def test_patient_cannot_submit_checkin_for_another_patient(client, db_session):
    a = _make_user(db_session, email="ca@swasthya.local")
    b = _make_user(db_session, email="cb@swasthya.local")

    resp = client.post(
        f"/api/patients/{a.id}/check-in",
        headers=_auth(b),
        json={"mood": 5, "energy": 5, "symptoms": []},
    )
    assert resp.status_code == 403


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
