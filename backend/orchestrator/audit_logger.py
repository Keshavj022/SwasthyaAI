"""
Audit Logger - Records all AI interactions for compliance and accountability.

Implements requirements from SAFETY_AND_SCOPE.md §7.2
All AI interactions MUST be logged to maintain audit trail.
"""

from sqlalchemy.orm import Session
from orchestrator.base import AgentRequest, AgentResponse
from typing import Optional, Dict, Any
from datetime import datetime
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.system import AuditLog

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Logs all AI interactions to database for compliance and review.
    """

    def log_interaction(
        self,
        db: Session,
        request: AgentRequest,
        response: AgentResponse,
        wrapped_response: Dict[str, Any],
        explainability_metadata: Optional[Dict[str, Any]] = None,
        escalation_triggered: Optional[str] = None,
        clinician_override: Optional[str] = None
    ) -> str:
        """
        Log an AI interaction to the audit trail with explainability metadata.

        Args:
            db: Database session
            request: Original user request
            response: Raw agent response
            wrapped_response: Safety-wrapped response
            explainability_metadata: Reasoning summaries and decision factors
            escalation_triggered: Type of escalation if any
            clinician_override: Override reason if clinician disagrees with AI

        Returns:
            audit_id: Unique ID for this audit log entry

        Raises:
            Exception: If database write fails
        """
        try:
            # De-identify input data (remove PII)
            input_data = self._deidentify_data({
                "message": request.message,
                "attachments": request.attachments,
                "context": request.context
            })

            # Prepare output data
            output_data = {
                "agent": response.agent_name,
                "data": response.data,
                "confidence": response.confidence,
                "reasoning": response.reasoning,
                "red_flags": response.red_flags,
                "requires_escalation": response.requires_escalation,
                "disclaimer_applied": wrapped_response.get("disclaimer", "")[:100]  # First 100 chars
            }

            # Extract explainability fields
            reasoning_summary = None
            decision_factors = None
            alternative_considerations = None
            explainability_score = None

            if explainability_metadata:
                reasoning_summary = explainability_metadata.get("reasoning_summary")
                decision_factors = explainability_metadata.get("decision_factors")
                alternative_considerations = explainability_metadata.get("alternative_considerations")
                explainability_score = explainability_metadata.get("explainability_score")

            # Extract safety flags
            safety_flags = None
            if wrapped_response.get("safety_check"):
                safety_flags = wrapped_response["safety_check"]

            # Create audit log entry with enhanced explainability fields
            audit_entry = AuditLog(
                timestamp=datetime.utcnow(),
                user_id=self._hash_user_id(request.user_id),  # Hashed for privacy
                agent_name=response.agent_name,
                action="agent_query",
                input_data=input_data,
                output_data=output_data,
                confidence_score=int(response.confidence * 100),
                # Enhanced explainability fields
                reasoning_summary=reasoning_summary,
                decision_factors=decision_factors,
                alternative_considerations=alternative_considerations,
                explainability_score=explainability_score,
                # Safety and escalation
                escalation_triggered=escalation_triggered,
                safety_flags=safety_flags,
                clinician_override=clinician_override
            )

            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)

            audit_id = f"audit_{audit_entry.timestamp.strftime('%Y%m%d')}_{audit_entry.id:05d}"

            logger.info(f"✓ Logged interaction: {audit_id} (explainability: {explainability_score or 'N/A'})")
            return audit_id

        except Exception as e:
            logger.error(f"Failed to log audit entry: {str(e)}")
            db.rollback()
            raise

    def log_safety_violation(
        self,
        db: Session,
        request: AgentRequest,
        violation_type: str,
        details: str
    ):
        """
        Log a safety violation (prohibited content, guardrail breach, etc.)

        Args:
            db: Database session
            request: Original request that caused violation
            violation_type: Type of violation (e.g., "prohibited_language")
            details: Details about the violation
        """
        try:
            audit_entry = AuditLog(
                timestamp=datetime.utcnow(),
                user_id=self._hash_user_id(request.user_id),
                agent_name="safety_agent",
                action="safety_violation",
                input_data=self._deidentify_data({"message": request.message}),
                output_data={
                    "violation_type": violation_type,
                    "details": details,
                    "blocked": True
                },
                confidence_score=None,
                escalation_triggered=violation_type
            )

            db.add(audit_entry)
            db.commit()

            logger.warning(f"✗ Safety violation logged: {violation_type}")

        except Exception as e:
            logger.error(f"Failed to log safety violation: {str(e)}")
            db.rollback()

    def log_clinician_override(
        self,
        db: Session,
        audit_id: str,
        clinician_id: str,
        override_reason: str,
        new_decision: str
    ):
        """
        Log when a clinician overrides an AI suggestion.

        Args:
            db: Database session
            audit_id: ID of original audit log entry
            clinician_id: ID of clinician making override
            override_reason: Why clinician disagrees with AI
            new_decision: Clinician's alternate decision
        """
        try:
            # Find original audit entry
            entry = db.query(AuditLog).filter(AuditLog.id == audit_id).first()

            if entry:
                entry.clinician_override = json.dumps({
                    "clinician_id": self._hash_user_id(clinician_id),
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": override_reason,
                    "new_decision": new_decision
                })
                db.commit()

                logger.info(f"✓ Clinician override logged for audit_id: {audit_id}")

        except Exception as e:
            logger.error(f"Failed to log clinician override: {str(e)}")
            db.rollback()

    def get_audit_log(self, db: Session, audit_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific audit log entry.

        Args:
            db: Database session
            audit_id: Audit log ID

        Returns:
            Dict with audit log data, or None if not found
        """
        try:
            # Extract numeric ID from audit_id string (e.g., "audit_20260131_00123" → 123)
            numeric_id = int(audit_id.split("_")[-1])

            entry = db.query(AuditLog).filter(AuditLog.id == numeric_id).first()

            if not entry:
                return None

            return {
                "audit_id": audit_id,
                "timestamp": entry.timestamp.isoformat(),
                "user_id": entry.user_id,  # Already hashed
                "agent_name": entry.agent_name,
                "action": entry.action,
                "input_data": entry.input_data,
                "output_data": entry.output_data,
                "confidence_score": entry.confidence_score,
                "escalation_triggered": entry.escalation_triggered,
                "clinician_override": entry.clinician_override
            }

        except Exception as e:
            logger.error(f"Failed to retrieve audit log: {str(e)}")
            return None

    def _deidentify_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove PII from data before storing in audit logs.

        Current implementation: Remove known PII fields
        Future: Use NLP-based PII detection

        Args:
            data: Raw data dict

        Returns:
            De-identified data dict
        """
        # Fields to remove (known PII)
        pii_fields = ["name", "email", "phone", "ssn", "address", "dob"]

        cleaned_data = {}
        for key, value in data.items():
            if key.lower() in pii_fields:
                cleaned_data[key] = "[REDACTED]"
            elif isinstance(value, dict):
                cleaned_data[key] = self._deidentify_data(value)
            elif isinstance(value, list):
                cleaned_data[key] = [
                    self._deidentify_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                cleaned_data[key] = value

        return cleaned_data

    def _hash_user_id(self, user_id: str) -> str:
        """
        Hash user ID for privacy protection in audit logs.

        Args:
            user_id: Raw user ID

        Returns:
            Hashed user ID
        """
        import hashlib
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]

    def get_agent_statistics(self, db: Session, agent_name: str) -> Dict[str, Any]:
        """
        Get usage statistics for a specific agent.

        Args:
            db: Database session
            agent_name: Name of agent

        Returns:
            Dict with statistics
        """
        try:
            total_queries = db.query(AuditLog).filter(
                AuditLog.agent_name == agent_name
            ).count()

            escalations = db.query(AuditLog).filter(
                AuditLog.agent_name == agent_name,
                AuditLog.escalation_triggered.isnot(None)
            ).count()

            overrides = db.query(AuditLog).filter(
                AuditLog.agent_name == agent_name,
                AuditLog.clinician_override.isnot(None)
            ).count()

            avg_confidence = db.query(AuditLog).filter(
                AuditLog.agent_name == agent_name,
                AuditLog.confidence_score.isnot(None)
            ).all()

            avg_conf_score = (
                sum([entry.confidence_score for entry in avg_confidence]) / len(avg_confidence)
                if avg_confidence else 0
            )

            return {
                "agent_name": agent_name,
                "total_queries": total_queries,
                "escalations": escalations,
                "clinician_overrides": overrides,
                "average_confidence": round(avg_conf_score, 2),
                "override_rate": round((overrides / total_queries * 100) if total_queries > 0 else 0, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get agent statistics: {str(e)}")
            return {}


# Global singleton instance
audit_logger = AuditLogger()
