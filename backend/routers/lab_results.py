"""
Lab Results API (Task 11).

Endpoints (mounted under /api by main.py):
- POST /lab-results/interpret    → interpret a set of lab values
- POST /lab-results/save         → persist a result set (owner-scoped)
- GET  /lab-results/{patient_id} → list saved result sets for a patient

Ownership model
---------------
Saved sets are keyed to the authenticated user's id (``owner_user_id``). A
patient may only save/read their OWN sets. Doctors and admins may read any
patient's saved sets. Ownership is always derived from the JWT — a client may
pass ``patient_id`` only as a label / filter, never as an authorization claim.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, JSON, String
from sqlalchemy.orm import Session
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Base, get_db
from models.user import User
from services.auth_service import get_current_user
from schemas.lab_results import (
    InterpretRequest,
    LabResultsResponse,
    SaveRequest,
    SaveResponse,
    SavedLabResultSet,
)
from agents.lab_results_agent import LabResultsAgent

router = APIRouter(prefix="/lab-results", tags=["lab-results"])

# Single shared agent instance (stateless, deterministic).
_agent = LabResultsAgent()


# ---------------------------------------------------------------------------
# Persistence model — registered with Base.metadata at import time so the
# table is created by init_db()/create_all() on startup (no migrations needed).
# ---------------------------------------------------------------------------

class LabResultSet(Base):
    """A saved set of lab results plus its cached interpretation."""

    __tablename__ = "lab_result_sets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id = Column(String, index=True, nullable=False)  # authenticated user
    patient_id = Column(String, index=True, nullable=True)      # optional label/filter

    lab_name = Column(String(200), nullable=True)
    report_date = Column(Date, nullable=True)

    results = Column(JSON, nullable=False)          # raw [{test_name,value,unit}]
    interpretation = Column(JSON, nullable=False)   # cached LabResultsResponse dict

    test_count = Column(Integer, default=0, nullable=False)
    has_critical = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _interpret(req_results, age: Optional[int], sex: Optional[str]) -> dict:
    """Run the agent's deterministic interpreter and return a plain dict."""
    return _agent.interpret_results(req_results, age, sex)


def _can_read_any(user: User) -> bool:
    return user.role in ("doctor", "admin")


def _serialize_set(row: LabResultSet) -> SavedLabResultSet:
    return SavedLabResultSet(
        id=row.id,
        patient_id=row.patient_id,
        lab_name=row.lab_name,
        report_date=row.report_date,
        created_at=row.created_at.isoformat() if row.created_at else "",
        test_count=row.test_count,
        has_critical=bool(row.has_critical),
        results=row.results or [],
        interpretation=LabResultsResponse(**(row.interpretation or {})),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/interpret", response_model=LabResultsResponse)
async def interpret_lab_results(
    payload: InterpretRequest,
    current_user: User = Depends(get_current_user),
) -> LabResultsResponse:
    """Interpret a set of lab values without persisting them."""
    interpretation = _interpret(payload.results, payload.patient_age, payload.patient_sex)
    return LabResultsResponse(**interpretation)


@router.post("/save", response_model=SaveResponse, status_code=201)
async def save_lab_results(
    payload: SaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SaveResponse:
    """
    Persist a lab result set scoped to the authenticated user.

    The interpretation is computed and cached at save time so history reloads
    are fast and stable.
    """
    interpretation = _interpret(payload.results, None, None)

    raw_results = [
        {"test_name": r.test_name, "value": r.value, "unit": r.unit}
        for r in payload.results
    ]
    has_critical = bool(interpretation.get("critical_flags"))

    row = LabResultSet(
        owner_user_id=str(current_user.id),
        patient_id=payload.patient_id,
        lab_name=payload.lab_name,
        report_date=payload.report_date,
        results=raw_results,
        interpretation=interpretation,
        test_count=len(raw_results),
        has_critical=has_critical,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return SaveResponse(id=row.id, saved=True)


@router.get("/{patient_id}", response_model=List[SavedLabResultSet])
async def get_saved_lab_results(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[SavedLabResultSet]:
    """
    Return saved lab result sets for ``patient_id``.

    Authorization:
    - Patients may only read sets they own (owner_user_id == their id).
    - Doctors / admins may read any patient's sets.

    ``patient_id`` is treated as a filter label; access is always governed by
    the authenticated identity, never by the path value alone.
    """
    q = db.query(LabResultSet)

    if _can_read_any(current_user):
        # Privileged readers: match by stored patient_id label OR by owner id
        # (covers sets saved without an explicit patient label).
        q = q.filter(
            (LabResultSet.patient_id == patient_id)
            | (LabResultSet.owner_user_id == patient_id)
        )
    else:
        # Patients: strictly their own records, regardless of the path value.
        q = q.filter(LabResultSet.owner_user_id == str(current_user.id))

    rows = q.order_by(LabResultSet.created_at.desc()).all()
    return [_serialize_set(r) for r in rows]
