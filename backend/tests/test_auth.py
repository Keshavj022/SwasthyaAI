"""
Authentication & authorization tests (Task 15).

Covers the public auth surface end-to-end with a FastAPI TestClient against an
isolated, throwaway SQLite database:

- register: creates a user, ALWAYS forced to the `patient` role, returns a token
- register: a client-supplied privileged `role` is ignored (cannot self-promote)
- register: duplicate email is rejected
- login: valid credentials return a token; wrong password / unknown email → 401
- /me: a valid token returns the user; missing / forged / "none"-alg tokens → 401
- role protection: a patient is forbidden from the admin-only /admin/users route

The app's normal startup seeds a default admin and registers agents via the
lifespan handler; we deliberately do NOT run the lifespan (which would write to
the real database). Instead we seed exactly the users each test needs.
"""

import sys
import uuid
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure the backend package root is importable when pytest is invoked from here.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import Base, get_db  # noqa: E402  (global Base / get_db dependency)
from models.user import User  # noqa: E402
from main import app  # noqa: E402
from services.auth_service import hash_password, create_access_token  # noqa: E402
from config import settings  # noqa: E402
from jose import jwt  # noqa: E402


# ---------------------------------------------------------------------------
# Isolated test database + dependency override
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_session():
    """A fresh in-memory SQLite database with all tables created."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared connection so :memory: persists
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
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
    """TestClient with get_db overridden to the isolated session."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    # NOTE: construct WITHOUT the context-manager form so the app lifespan
    # (which seeds a default admin into the real database and preloads models)
    # does not run during tests. Routes are fully exercisable without it.
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(db_session, role="patient", email=None, password="Patient@1234"):
    user = User(
        email=email or f"{role}.{uuid.uuid4().hex[:8]}@swasthya.local",
        hashed_password=hash_password(password),
        full_name=f"Test {role.title()}",
        role=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_creates_patient_and_returns_token(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "newpatient@swasthya.local",
            "password": "Secret123",
            "full_name": "New Patient",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "newpatient@swasthya.local"
    assert body["user"]["role"] == "patient"
    assert body["user"]["is_active"] is True


def test_register_ignores_client_supplied_role(client):
    """A client cannot self-provision an admin/doctor account via /register."""
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "wannabe.admin@swasthya.local",
            "password": "Secret123",
            "full_name": "Wannabe Admin",
            "role": "admin",  # must be ignored
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["user"]["role"] == "patient"

    # The minted token must also carry the patient role, not admin.
    token = resp.json()["access_token"]
    decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert decoded.get("role") == "patient"


def test_register_duplicate_email_rejected(client):
    payload = {
        "email": "dup@swasthya.local",
        "password": "Secret123",
        "full_name": "First",
    }
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 400


def test_register_weak_password_rejected(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "weak@swasthya.local",
            "password": "short",  # < 8 chars and no digit
            "full_name": "Weak Password",
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_valid_credentials_returns_token(client, db_session):
    _make_user(db_session, role="patient", email="login.ok@swasthya.local",
               password="GoodPass1")
    resp = client.post(
        "/api/auth/login",
        json={"email": "login.ok@swasthya.local", "password": "GoodPass1"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["access_token"]


def test_login_wrong_password_returns_401(client, db_session):
    _make_user(db_session, email="login.bad@swasthya.local", password="GoodPass1")
    resp = client.post(
        "/api/auth/login",
        json={"email": "login.bad@swasthya.local", "password": "WrongPass9"},
    )
    assert resp.status_code == 401


def test_login_unknown_email_returns_401(client):
    resp = client.post(
        "/api/auth/login",
        json={"email": "ghost@swasthya.local", "password": "Whatever1"},
    )
    assert resp.status_code == 401


def test_login_disabled_account_returns_403(client, db_session):
    user = _make_user(db_session, email="disabled@swasthya.local", password="GoodPass1")
    user.is_active = False
    db_session.commit()
    resp = client.post(
        "/api/auth/login",
        json={"email": "disabled@swasthya.local", "password": "GoodPass1"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# /me  +  token validation
# ---------------------------------------------------------------------------

def test_me_with_valid_token(client, db_session):
    user = _make_user(db_session, email="me@swasthya.local", password="GoodPass1")
    token = create_access_token({"sub": user.id, "role": user.role})
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == "me@swasthya.local"


def test_me_without_token_is_401(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_garbage_token_is_401(client):
    resp = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"}
    )
    assert resp.status_code == 401


def test_me_with_forged_token_is_401(client, db_session):
    """A token signed with the WRONG secret must be rejected."""
    user = _make_user(db_session, email="forge@swasthya.local")
    forged = jwt.encode(
        {"sub": user.id, "role": "admin"},
        "attacker-controlled-secret",
        algorithm="HS256",
    )
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401


def test_me_with_alg_none_token_is_401(client, db_session):
    """An unsigned ('alg: none') token must be rejected.

    Crafted by hand because the library refuses to *encode* alg=none; what we are
    testing is that the server refuses to *decode/trust* such a token.
    """
    import base64
    import json

    def _b64(d: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()

    user = _make_user(db_session, email="algnone@swasthya.local")
    unsigned = (
        _b64({"alg": "none", "typ": "JWT"})
        + "."
        + _b64({"sub": user.id, "role": "admin"})
        + "."
    )
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {unsigned}"})
    assert resp.status_code == 401


def test_me_with_expired_token_is_401(client, db_session):
    user = _make_user(db_session, email="expired@swasthya.local")
    expired = create_access_token(
        {"sub": user.id, "role": user.role}, expires_delta=timedelta(minutes=-5)
    )
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Role protection
# ---------------------------------------------------------------------------

def test_patient_cannot_access_admin_users(client, db_session):
    user = _make_user(db_session, role="patient", email="plain@swasthya.local")
    token = create_access_token({"sub": user.id, "role": user.role})
    resp = client.get(
        "/api/admin/users", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_admin_can_access_admin_users(client, db_session):
    admin = _make_user(db_session, role="admin", email="boss@swasthya.local")
    token = create_access_token({"sub": admin.id, "role": admin.role})
    resp = client.get(
        "/api/admin/users", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
    emails = [u["email"] for u in resp.json()]
    assert "boss@swasthya.local" in emails


def test_admin_users_requires_auth(client):
    resp = client.get("/api/admin/users")
    assert resp.status_code == 401


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
