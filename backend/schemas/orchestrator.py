"""
Pydantic schemas for orchestrator API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class QueryRequest(BaseModel):
    """
    Request schema for /api/orchestrator/query endpoint.

    SECURITY: user_id is IGNORED if supplied — the authenticated user's id is
    always derived from the JWT server-side. The optional field is kept only for
    backward compatibility with older clients and never trusted.
    """
    user_id: Optional[str] = Field(default=None, description="(Ignored) derived from auth token server-side")
    message: Optional[str] = Field(default="", description="User query or message")
    attachments: Optional[List[str]] = Field(default=[], description="List of attachment IDs (images, files)")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context (user_type, session_id, etc.)")
    # Voice input (Task 12) — base64-encoded audio routed to the voice agent
    audio_base64: Optional[str] = Field(default=None, description="Base64-encoded audio for transcription")
    audio_format: Optional[str] = Field(default=None, description="Audio container/format, e.g. 'webm', 'wav'")
    voice_mode: Optional[str] = Field(default=None, description="symptom_reporting | medical_dictation | voice_query | general")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "patient_123",
                "message": "I have a fever of 102°F and a persistent cough",
                "attachments": [],
                "context": {
                    "user_type": "patient",
                    "age": 34,
                    "gender": "F",
                    "session_id": "session_abc123"
                }
            }
        }


class QueryResponse(BaseModel):
    """
    Response schema for /api/orchestrator/query endpoint
    """
    success: bool
    agent: Optional[str] = None
    timestamp: str
    confidence: Optional[Dict[str, Any]] = None
    data: Dict[str, Any]
    reasoning: Optional[str] = None
    disclaimer: str
    audit_id: Optional[str] = None
    emergency: Optional[bool] = False
    intent: Optional[Dict[str, Any]] = None
    safety_check: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "agent": "triage",
                "timestamp": "2026-01-31T10:30:00Z",
                "confidence": {
                    "score": 78,
                    "level": "moderate",
                    "emoji": "🟡"
                },
                "data": {
                    "urgency_level": "ROUTINE",
                    "recommendation": "Schedule routine clinic visit"
                },
                "reasoning": "No immediate red flags detected",
                "disclaimer": "⚠️ CLINICAL DECISION SUPPORT NOTICE...",
                "audit_id": "audit_20260131_00123",
                "emergency": False
            }
        }


class AgentInfo(BaseModel):
    """Agent metadata"""
    name: str
    description: str
    capabilities: List[str]
    enabled: bool
    confidence_threshold: float


class AgentsListResponse(BaseModel):
    """Response for /api/orchestrator/agents endpoint"""
    total_agents: int
    agents: List[AgentInfo]


class AuditLogResponse(BaseModel):
    """Response for /api/orchestrator/audit/{audit_id} endpoint"""
    audit_id: str
    timestamp: str
    user_id: str
    agent_name: str
    action: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    confidence_score: Optional[int]
    escalation_triggered: Optional[str]
    clinician_override: Optional[str]


class OrchestratorHealthResponse(BaseModel):
    """Health check response for orchestrator"""
    status: str
    total_agents: int
    enabled_agents: int
    classifier: str
    safety_wrapper: str
    audit_logger: str
