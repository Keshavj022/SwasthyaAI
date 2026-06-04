"""
Pydantic schemas for the Lab Results Agent / API (Task 11).

Defines the request/response contract for interpreting, saving and retrieving
laboratory result sets. Mirrors the response schema described in the task spec.
"""

from __future__ import annotations

from datetime import date as date_type
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

ResultStatus = Literal["normal", "low", "high", "critical"]


class LabResultInput(BaseModel):
    """A single lab measurement supplied by the client."""

    test_name: str = Field(..., min_length=1, max_length=120,
                           description="Test identifier, e.g. 'hba1c', 'potassium'")
    value: float = Field(..., description="Numeric measured value")
    unit: Optional[str] = Field(default=None, max_length=40,
                                description="Unit of measurement, e.g. '%', 'mg/dL'")

    @field_validator("test_name")
    @classmethod
    def _normalize_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("value")
    @classmethod
    def _sane_value(cls, v: float) -> float:
        # Reject obviously impossible values; lab numbers are non-negative and
        # bounded well below this for every test we model.
        if v != v:  # NaN guard
            raise ValueError("value must be a finite number")
        if v < 0:
            raise ValueError("value must be non-negative")
        if v > 1_000_000:
            raise ValueError("value is implausibly large")
        return v


# ---------------------------------------------------------------------------
# Interpretation request
# ---------------------------------------------------------------------------

class InterpretRequest(BaseModel):
    """Body for POST /api/lab-results/interpret."""

    results: List[LabResultInput] = Field(..., min_length=1, max_length=40)
    patient_id: Optional[str] = Field(default=None, max_length=80)
    patient_age: Optional[int] = Field(default=None, ge=0, le=130)
    patient_sex: Optional[str] = Field(default=None, max_length=20)

    @field_validator("patient_sex")
    @classmethod
    def _normalize_sex(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return v.strip().lower()


# ---------------------------------------------------------------------------
# Interpreted output
# ---------------------------------------------------------------------------

class InterpretedResult(BaseModel):
    """A single interpreted result row."""

    test_name: str
    value: float
    unit: str
    status: ResultStatus
    reference_range: str
    explanation: str
    action_needed: bool = False


class LabResultsResponse(BaseModel):
    """Full interpretation payload returned to the client."""

    results: List[InterpretedResult] = Field(default_factory=list)
    summary: str = ""
    patterns_detected: List[str] = Field(default_factory=list)
    critical_flags: List[str] = Field(default_factory=list)
    follow_up_tests: List[str] = Field(default_factory=list)
    disclaimer: str = ""
    stub_mode: bool = False


# ---------------------------------------------------------------------------
# Persistence (save / history)
# ---------------------------------------------------------------------------

class SaveRequest(BaseModel):
    """Body for POST /api/lab-results/save."""

    patient_id: Optional[str] = Field(default=None, max_length=80)
    results: List[LabResultInput] = Field(..., min_length=1, max_length=40)
    report_date: Optional[date_type] = Field(default=None,
                                             description="Date the report was issued")
    lab_name: Optional[str] = Field(default=None, max_length=200)


class SaveResponse(BaseModel):
    """Response for POST /api/lab-results/save."""

    id: str
    saved: bool = True


class SavedLabResultSet(BaseModel):
    """A previously saved lab result set with its interpretation."""

    id: str
    patient_id: Optional[str] = None
    lab_name: Optional[str] = None
    report_date: Optional[date_type] = None
    created_at: str
    test_count: int
    has_critical: bool
    results: List[LabResultInput] = Field(default_factory=list)
    interpretation: LabResultsResponse
