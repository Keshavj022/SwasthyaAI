"""
Orchestrator API routes.

Main endpoints for agent interactions:
- POST /query - Send query to orchestrator
- GET /agents - List available agents
- GET /audit/{audit_id} - Retrieve audit log
- GET /health - Orchestrator health check
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from schemas.orchestrator import (
    QueryRequest,
    QueryResponse,
    AgentsListResponse,
    AgentInfo,
    AuditLogResponse,
    OrchestratorHealthResponse
)
from orchestrator.base import AgentRequest
from orchestrator.orchestrator import orchestrator

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@router.post("/query", response_model=QueryResponse)
async def query_orchestrator(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Main orchestrator endpoint - processes user queries through agent system.

    Workflow:
    1. Classify intent → Determine which agent to use
    2. Execute agent → Generate response
    3. Apply safety wrapper → Add disclaimers, check guardrails
    4. Log to audit trail → Record interaction
    5. Return wrapped response → Send to user

    Args:
        request: QueryRequest with user message and context
        db: Database session for audit logging

    Returns:
        QueryResponse with agent output and safety measures

    Example:
        ```
        POST /api/orchestrator/query
        {
            "user_id": "patient_123",
            "message": "I have a fever and cough",
            "context": {"user_type": "patient"}
        }
        ```
    """
    # Convert to AgentRequest
    agent_request = AgentRequest(
        user_id=request.user_id,
        message=request.message,
        attachments=request.attachments or [],
        context=request.context or {}
    )

    # Process through orchestrator
    response = await orchestrator.process_request(agent_request, db)

    return response


@router.get("/agents", response_model=AgentsListResponse)
async def list_agents():
    """
    List all available agents and their capabilities.

    Returns:
        AgentsListResponse with agent metadata

    Example Response:
        ```json
        {
            "total_agents": 5,
            "agents": [
                {
                    "name": "triage",
                    "description": "Emergency triage and urgency classification",
                    "capabilities": ["emergency", "urgent", "symptoms"],
                    "enabled": true,
                    "confidence_threshold": 0.60
                },
                ...
            ]
        }
        ```
    """
    agents_info = orchestrator.get_available_agents()

    return {
        "total_agents": len(agents_info),
        "agents": [
            AgentInfo(
                name=agent["name"],
                description=agent["description"],
                capabilities=agent["capabilities"],
                enabled=agent["enabled"],
                confidence_threshold=agent["confidence_threshold"]
            )
            for agent in agents_info
        ]
    }


@router.get("/audit/{audit_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve audit log for a specific interaction.

    Args:
        audit_id: Unique audit log identifier (e.g., "audit_20260131_00123")
        db: Database session

    Returns:
        AuditLogResponse with full audit trail

    Raises:
        HTTPException 404: If audit log not found

    Example:
        ```
        GET /api/orchestrator/audit/audit_20260131_00123
        ```
    """
    from orchestrator.audit_logger import audit_logger

    log_entry = audit_logger.get_audit_log(db, audit_id)

    if not log_entry:
        raise HTTPException(
            status_code=404,
            detail=f"Audit log '{audit_id}' not found"
        )

    return AuditLogResponse(**log_entry)


@router.get("/health", response_model=OrchestratorHealthResponse)
async def orchestrator_health():
    """
    Check orchestrator system health.

    Returns:
        OrchestratorHealthResponse with system status

    Example Response:
        ```json
        {
            "status": "healthy",
            "total_agents": 5,
            "enabled_agents": 5,
            "classifier": "active",
            "safety_wrapper": "active",
            "audit_logger": "active"
        }
        ```
    """
    health = orchestrator.health_check()
    return OrchestratorHealthResponse(**health)


@router.get("/agent/{agent_name}/stats")
async def get_agent_statistics(
    agent_name: str,
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for a specific agent.

    Args:
        agent_name: Name of agent (e.g., "triage", "diagnostic_support")
        db: Database session

    Returns:
        Dict with agent statistics

    Example Response:
        ```json
        {
            "agent_name": "triage",
            "total_queries": 150,
            "escalations": 12,
            "clinician_overrides": 5,
            "average_confidence": 76.5,
            "override_rate": 3.33
        }
        ```
    """
    from orchestrator.audit_logger import audit_logger

    stats = audit_logger.get_agent_statistics(db, agent_name)

    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"No statistics found for agent '{agent_name}'"
        )

    return stats
