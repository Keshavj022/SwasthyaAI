from pydantic import BaseModel, Field
from typing import Optional, Literal


class LabResultInput(BaseModel):
    test_name: str  # e.g. "hba1c", "hemoglobin", or any free-text
    value: float
    unit: str
    date: Optional[str] = None  # ISO date string, optional


class InterpretedResult(BaseModel):
    test_name: str
    value: float
    unit: str
    status: Literal["normal", "low", "high", "critical"]
    reference_range: str
    explanation: str
    action_needed: bool


class LabResultsResponse(BaseModel):
    results: list[InterpretedResult]
    summary: str
    patterns_detected: list[str]
    critical_flags: list[str]
    follow_up_tests: list[str]
    disclaimer: str


class InterpretRequest(BaseModel):
    results: list[LabResultInput]
    patient_id: str
    patient_age: int = Field(ge=1, le=120)
    patient_sex: Literal["male", "female", "other"] = "other"


class SaveLabReportRequest(BaseModel):
    patient_id: str
    results: list[LabResultInput]
    report_date: str  # ISO date string
    lab_name: str = ""
    patient_age: int = Field(ge=1, le=120)
    patient_sex: Literal["male", "female", "other"] = "other"


class SavedLabReport(BaseModel):
    id: str
    patient_id: str
    report_date: str
    lab_name: str
    test_count: int
    has_critical: bool
    created_at: str
    results: list[LabResultInput]
