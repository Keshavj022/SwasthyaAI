"""
Main Orchestrator Service - Coordinates all agent interactions.

This is the central coordinator that:
1. Receives user requests
2. Classifies intent
3. Routes to appropriate agent(s)
4. Applies safety wrapper
5. Logs to audit trail
6. Returns safe response to user
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from orchestrator.base import AgentRequest, AgentResponse
from orchestrator.registry import registry
from orchestrator.intent_classifier import classifier, IntentClassification
from orchestrator.safety_wrapper import safety_wrapper, SafetyViolation
from orchestrator.audit_logger import audit_logger
import logging
import traceback

logger = logging.getLogger(__name__)

# Import explainability agent for generating reasoning summaries
from agents.explainability_agent import ExplainabilityAgent
_explainability_agent = ExplainabilityAgent()


class OrchestratorError(Exception):
    """Raised when orchestration fails"""
    pass


class Orchestrator:
    """
    Main orchestrator service that coordinates multi-agent system.
    """

    def __init__(self):
        self.registry = registry
        self.classifier = classifier
        self.safety_wrapper = safety_wrapper
        self.audit_logger = audit_logger

    async def process_request(
        self,
        request: AgentRequest,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process user request through full orchestrator pipeline.

        Pipeline:
        1. Validate request
        2. Classify intent → Determine agent(s)
        3. Route to agent(s) → Execute
        4. Apply safety wrapper → Inject disclaimers, check guardrails
        5. Log to audit trail → Record interaction
        6. Return wrapped response

        Args:
            request: User request
            db: Database session for audit logging

        Returns:
            Dict with wrapped response

        Raises:
            OrchestratorError: If orchestration fails
        """
        try:
            # Step 1: Validate request
            if not request.message or len(request.message.strip()) == 0:
                return self._error_response("Empty message. Please provide a valid query.")

            logger.info(f"Processing request from user: {request.user_id}")

            # Step 2: Classify intent
            intent = self.classifier.classify(request)
            logger.info(f"Intent classified: {intent}")

            # Step 2.5: Add context from intent classification
            # This helps agents understand what type of request this is
            if not request.context:
                request.context = {}
            
            # Add message as question for communication agent if needed
            if intent.primary_agent == "communication" and "question" not in request.context:
                request.context["question"] = request.message
            
            # Step 3: Get agent from registry
            agent = self.registry.get(intent.primary_agent)

            if not agent:
                return self._error_response(
                    f"Agent '{intent.primary_agent}' not found. "
                    f"Please check agent registry."
                )

            if not agent.is_enabled():
                return self._error_response(
                    f"Agent '{intent.primary_agent}' is currently disabled."
                )

            # Step 4: Execute agent
            logger.info(f"Executing agent: {agent.get_name()}")
            agent_response = await agent.process(request)

            # Step 5: Apply safety wrapper
            try:
                wrapped_response = self.safety_wrapper.wrap_response(
                    agent_response,
                    agent_type=intent.primary_agent
                )
            except SafetyViolation as e:
                # Safety violation detected - log and block
                logger.error(f"Safety violation: {str(e)}")
                self.audit_logger.log_safety_violation(
                    db=db,
                    request=request,
                    violation_type="prohibited_language",
                    details=str(e)
                )
                return self._error_response(
                    "The AI generated a response that violates safety boundaries. "
                    "This has been logged. Please rephrase your query."
                )
            except Exception as e:
                # Catch any errors in safety wrapper (e.g., type errors)
                logger.error(f"Error in safety wrapper: {str(e)}")
                logger.error(traceback.format_exc())
                return self._error_response(
                    f"An error occurred while applying safety checks. Error: {str(e)}"
                )

            # Step 6: Generate explainability metadata
            explainability_metadata = _explainability_agent.explain_agent_response(
                agent_response,
                agent_type=intent.primary_agent
            )
            logger.info(f"Generated explainability metadata (score: {explainability_metadata.get('explainability_score', 0)})")

            # Step 7: Log to audit trail with explainability
            escalation = wrapped_response.get("emergency_alert") if wrapped_response.get("emergency") else None
            audit_id = self.audit_logger.log_interaction(
                db=db,
                request=request,
                response=agent_response,
                wrapped_response=wrapped_response,
                explainability_metadata=explainability_metadata,
                escalation_triggered=escalation
            )

            # Step 8: Add audit ID to response
            wrapped_response["audit_id"] = audit_id

            # Step 9: Add explainability metadata to response (optional - for transparency)
            wrapped_response["explainability"] = {
                "score": explainability_metadata.get("explainability_score", 0),
                "reasoning_available": bool(explainability_metadata.get("reasoning_summary"))
            }

            # Step 10: Add intent classification metadata
            wrapped_response["intent"] = intent.to_dict()

            logger.info(f"✓ Request processed successfully. Audit ID: {audit_id}")
            return wrapped_response

        except Exception as e:
            logger.error(f"Orchestrator error: {str(e)}")
            logger.error(traceback.format_exc())
            return self._error_response(
                f"An error occurred while processing your request. "
                f"Error: {str(e)}"
            )

    async def process_multi_agent(
        self,
        request: AgentRequest,
        agent_names: list,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process request through multiple agents in parallel.

        Future enhancement: Execute agents in parallel using asyncio.gather()

        Args:
            request: User request
            agent_names: List of agent names to invoke
            db: Database session

        Returns:
            Dict with aggregated responses from all agents
        """
        responses = {}

        for agent_name in agent_names:
            agent = self.registry.get(agent_name)
            if agent and agent.is_enabled():
                try:
                    response = await agent.process(request)
                    wrapped = self.safety_wrapper.wrap_response(response, agent_type=agent_name)
                    responses[agent_name] = wrapped
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {str(e)}")
                    responses[agent_name] = {"error": str(e)}

        return {
            "success": True,
            "multi_agent": True,
            "agents": list(responses.keys()),
            "responses": responses
        }

    def get_available_agents(self) -> list:
        """
        Get list of all available agents with metadata.

        Returns:
            List of agent info dicts
        """
        return self.registry.get_agent_info()

    def get_agent_by_capability(self, capability: str) -> list:
        """
        Find agents that handle a specific capability.

        Args:
            capability: Capability keyword

        Returns:
            List of agent names
        """
        agents = self.registry.get_by_capability(capability)
        return [agent.get_name() for agent in agents]

    def health_check(self) -> Dict[str, Any]:
        """
        Check orchestrator health and readiness.

        Returns:
            Dict with health status
        """
        total_agents = len(self.registry)
        enabled_agents = len(self.registry.list_enabled())

        return {
            "status": "healthy" if enabled_agents > 0 else "degraded",
            "total_agents": total_agents,
            "enabled_agents": enabled_agents,
            "classifier": "active",
            "safety_wrapper": "active",
            "audit_logger": "active"
        }

    def _error_response(self, message: str) -> Dict[str, Any]:
        """
        Generate standardized error response.

        Args:
            message: Error message

        Returns:
            Error response dict
        """
        from datetime import datetime
        return {
            "success": False,
            "agent": None,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": None,
            "data": {
                "error": message
            },
            "reasoning": None,
            "disclaimer": self.safety_wrapper.disclaimers["general"],
            "audit_id": None,
            "emergency": False,
            "intent": None,
            "safety_check": None
        }


# Global singleton instance
orchestrator = Orchestrator()
