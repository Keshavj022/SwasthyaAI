"""
Audit Log API routes - Enhanced query and review endpoints.

Provides comprehensive audit trail access for clinician review and compliance.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models.system import AuditLog
from agents.explainability_agent import ExplainabilityAgent

router = APIRouter(prefix="/audit", tags=["audit"])

# Initialize explainability agent for formatting summaries
_explainability_agent = ExplainabilityAgent()


@router.get("/logs")
async def query_audit_logs(
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    user_id: Optional[str] = Query(None, description="Filter by hashed user ID"),
    min_confidence: Optional[int] = Query(None, ge=0, le=100, description="Minimum confidence score"),
    escalations_only: Optional[bool] = Query(False, description="Only show escalations"),
    hours: Optional[int] = Query(24, ge=1, le=168, description="Logs from last N hours"),
    limit: Optional[int] = Query(50, ge=1, le=500, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Query audit logs with flexible filtering.

    Filters:
    - agent_name: Filter by specific agent
    - user_id: Filter by hashed user ID
    - min_confidence: Only show results above this confidence
    - escalations_only: Only show entries that triggered escalation
    - hours: Logs from last N hours (default: 24)
    - limit: Maximum results to return (default: 50)

    Returns:
        List of audit log entries matching filters

    Example:
        ```
        GET /api/audit/logs?agent_name=triage&escalations_only=true&hours=48
        ```
    """
    # Build query
    query = db.query(AuditLog)

    # Apply filters
    if agent_name:
        query = query.filter(AuditLog.agent_name == agent_name)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if min_confidence is not None:
        query = query.filter(AuditLog.confidence_score >= min_confidence)

    if escalations_only:
        query = query.filter(AuditLog.escalation_triggered.isnot(None))

    # Time filter
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(AuditLog.timestamp >= since)

    # Order by most recent first
    query = query.order_by(AuditLog.timestamp.desc())

    # Limit results
    logs = query.limit(limit).all()

    # Format results
    results = []
    for log in logs:
        results.append({
            "audit_id": f"audit_{log.timestamp.strftime('%Y%m%d')}_{log.id:05d}",
            "timestamp": log.timestamp.isoformat(),
            "agent_name": log.agent_name,
            "confidence_score": log.confidence_score,
            "explainability_score": log.explainability_score,
            "escalation_triggered": log.escalation_triggered,
            "reasoning_summary": log.reasoning_summary,
            "reviewed": bool(log.reviewed_by)
        })

    return {
        "total_results": len(results),
        "filters_applied": {
            "agent_name": agent_name,
            "min_confidence": min_confidence,
            "escalations_only": escalations_only,
            "hours": hours
        },
        "logs": results
    }


@router.get("/logs/{audit_id}/full")
async def get_full_audit_log(
    audit_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete audit log entry with all fields.

    Args:
        audit_id: Audit log identifier (e.g., "audit_20260131_00123")

    Returns:
        Complete audit log entry with all explainability metadata

    Example:
        ```
        GET /api/audit/logs/audit_20260131_00123/full
        ```
    """
    # Extract numeric ID from audit_id
    try:
        numeric_id = int(audit_id.split("_")[-1])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid audit_id format")

    log = db.query(AuditLog).filter(AuditLog.id == numeric_id).first()

    if not log:
        raise HTTPException(status_code=404, detail=f"Audit log '{audit_id}' not found")

    return {
        "audit_id": audit_id,
        "timestamp": log.timestamp.isoformat(),
        "user_id": log.user_id,
        "agent_name": log.agent_name,
        "action": log.action,
        "input_data": log.input_data,
        "output_data": log.output_data,
        "confidence_score": log.confidence_score,
        "explainability_score": log.explainability_score,
        "reasoning_summary": log.reasoning_summary,
        "decision_factors": log.decision_factors,
        "alternative_considerations": log.alternative_considerations,
        "escalation_triggered": log.escalation_triggered,
        "safety_flags": log.safety_flags,
        "clinician_override": log.clinician_override,
        "reviewed_by": log.reviewed_by,
        "review_timestamp": log.review_timestamp.isoformat() if log.review_timestamp else None,
        "review_notes": log.review_notes
    }


@router.get("/logs/{audit_id}/summary")
async def get_audit_summary(
    audit_id: str,
    db: Session = Depends(get_db)
):
    """
    Get human-readable audit summary for clinician review.

    This endpoint formats the audit log entry as a readable summary
    suitable for display in a review interface.

    Args:
        audit_id: Audit log identifier

    Returns:
        Human-readable summary text

    Example:
        ```
        GET /api/audit/logs/audit_20260131_00123/summary
        ```
    """
    # Extract numeric ID
    try:
        numeric_id = int(audit_id.split("_")[-1])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid audit_id format")

    log = db.query(AuditLog).filter(AuditLog.id == numeric_id).first()

    if not log:
        raise HTTPException(status_code=404, detail=f"Audit log '{audit_id}' not found")

    # Convert to dict for formatting
    audit_dict = {
        "audit_id": audit_id,
        "timestamp": log.timestamp.isoformat(),
        "user_id": log.user_id,
        "agent_name": log.agent_name,
        "action": log.action,
        "input_data": log.input_data,
        "output_data": log.output_data,
        "confidence_score": log.confidence_score,
        "explainability_score": log.explainability_score,
        "reasoning_summary": log.reasoning_summary,
        "decision_factors": log.decision_factors,
        "alternative_considerations": log.alternative_considerations,
        "escalation_triggered": log.escalation_triggered,
        "clinician_override": log.clinician_override
    }

    # Generate human-readable summary
    summary_text = _explainability_agent.format_audit_summary(audit_dict)

    return {
        "audit_id": audit_id,
        "summary": summary_text,
        "agent_name": log.agent_name,
        "timestamp": log.timestamp.isoformat(),
        "requires_review": not bool(log.reviewed_by),
        "explainability_score": log.explainability_score
    }


@router.post("/logs/{audit_id}/review")
async def mark_log_reviewed(
    audit_id: str,
    clinician_id: str = Query(..., description="Clinician ID performing review"),
    notes: Optional[str] = Query(None, description="Review notes"),
    override: Optional[bool] = Query(False, description="Did clinician override AI decision?"),
    override_reason: Optional[str] = Query(None, description="Reason for override"),
    db: Session = Depends(get_db)
):
    """
    Mark audit log as reviewed by clinician.

    Use this endpoint when a clinician has reviewed an AI decision and
    wants to record their review in the audit trail.

    Args:
        audit_id: Audit log identifier
        clinician_id: ID of reviewing clinician
        notes: Optional review notes
        override: Whether clinician overrode AI decision
        override_reason: Reason for override (required if override=true)

    Returns:
        Updated audit log status

    Example:
        ```
        POST /api/audit/logs/audit_20260131_00123/review?clinician_id=dr_smith&notes=Reviewed%20and%20approved
        ```
    """
    # Validate override
    if override and not override_reason:
        raise HTTPException(
            status_code=400,
            detail="override_reason is required when override=true"
        )

    # Extract numeric ID
    try:
        numeric_id = int(audit_id.split("_")[-1])
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid audit_id format")

    log = db.query(AuditLog).filter(AuditLog.id == numeric_id).first()

    if not log:
        raise HTTPException(status_code=404, detail=f"Audit log '{audit_id}' not found")

    # Hash clinician ID for privacy
    import hashlib
    hashed_clinician_id = hashlib.sha256(clinician_id.encode()).hexdigest()[:16]

    # Update review fields
    log.reviewed_by = hashed_clinician_id
    log.review_timestamp = datetime.utcnow()
    log.review_notes = notes

    if override:
        log.clinician_override = override_reason

    db.commit()

    return {
        "audit_id": audit_id,
        "reviewed": True,
        "reviewed_by": hashed_clinician_id,
        "review_timestamp": log.review_timestamp.isoformat(),
        "override_recorded": override
    }


@router.get("/stats/explainability")
async def get_explainability_statistics(
    days: Optional[int] = Query(7, ge=1, le=90, description="Stats from last N days"),
    db: Session = Depends(get_db)
):
    """
    Get explainability statistics across all agents.

    Returns metrics about how explainable AI decisions have been
    over the specified time period.

    Args:
        days: Number of days to include in statistics (default: 7)

    Returns:
        Explainability metrics

    Example:
        ```
        GET /api/audit/stats/explainability?days=30
        ```
    """
    since = datetime.utcnow() - timedelta(days=days)

    logs = db.query(AuditLog).filter(
        AuditLog.timestamp >= since,
        AuditLog.explainability_score.isnot(None)
    ).all()

    if not logs:
        return {
            "period_days": days,
            "total_logs": 0,
            "message": "No logs with explainability scores found"
        }

    scores = [log.explainability_score for log in logs if log.explainability_score]
    avg_score = sum(scores) / len(scores) if scores else 0

    # Count by score ranges
    high_explain = len([s for s in scores if s >= 80])
    moderate_explain = len([s for s in scores if 50 <= s < 80])
    low_explain = len([s for s in scores if s < 50])

    return {
        "period_days": days,
        "total_logs": len(logs),
        "average_explainability_score": round(avg_score, 2),
        "distribution": {
            "high_explainability": {
                "count": high_explain,
                "percentage": round(high_explain / len(logs) * 100, 2)
            },
            "moderate_explainability": {
                "count": moderate_explain,
                "percentage": round(moderate_explain / len(logs) * 100, 2)
            },
            "low_explainability": {
                "count": low_explain,
                "percentage": round(low_explain / len(logs) * 100, 2)
            }
        }
    }
