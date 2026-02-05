"""
Example: Communication Agent Integration with MedGemma

This file shows how to integrate MedGemma into the Communication Agent.
Replace stub responses with real AI inference while maintaining the same interface.

BEFORE: Uses _generate_stub_response()
AFTER: Uses MedGemmaInference.generate_response()
"""

from typing import Dict, Any, Optional
from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
from inference.medgemma import MedGemmaInference
from config import settings


class CommunicationAgentWithAI(BaseAgent):
    """
    Communication Agent with MedGemma Integration

    Handles medical Q&A, general health queries, and medical information requests
    using Google's MedGemma model for real medical reasoning.
    """

    def __init__(self):
        super().__init__()
        self.name = "communication"

        # Initialize MedGemma inference (lazy loading on first use)
        self.model_inference = MedGemmaInference(
            model_path=settings.MEDGEMMA_MODEL_PATH,
            device=settings.MODEL_DEVICE
        )

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process communication requests using MedGemma

        Args:
            request: Incoming request with query and context

        Returns:
            AgentResponse with AI-generated medical information
        """
        query = request.message
        context = request.context or {}

        # Determine task type from context
        task_type = context.get("task", "medical_qa")

        # Get patient context if available
        patient_context = self._extract_patient_context(context)

        try:
            # === THIS IS THE KEY CHANGE ===
            # OLD: response_data = self._generate_stub_response(query)
            # NEW: Use MedGemma for real inference

            response_data = await self.model_inference.generate_response(
                query=query,
                patient_context=patient_context,
                task_type=task_type,
                max_length=settings.MAX_GENERATION_LENGTH,
                temperature=settings.TEMPERATURE
            )

            # Extract key fields from model response
            analysis = response_data.get("analysis_summary", "")
            confidence = response_data.get("confidence", 0.5)
            disclaimer = response_data.get("disclaimer", "")

            # Check if using stub (model not available)
            using_stub = response_data.get("stub_mode", False)

            # Build agent response
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data={
                    "response": analysis,
                    "key_findings": response_data.get("key_findings", []),
                    "recommended_next_steps": response_data.get("recommended_next_steps", []),
                    "disclaimer": disclaimer,
                    "model_used": "MedGemma" if not using_stub else "Stub",
                    "model_info": self.model_inference.get_model_info()
                },
                confidence=confidence,
                reasoning=f"Medical QA response generated using {'MedGemma AI model' if not using_stub else 'rule-based stub'}"
            )

        except Exception as e:
            # Fallback to error response
            return AgentResponse(
                agent_name=self.name,
                success=False,
                data={
                    "error": f"Failed to process query: {str(e)}",
                    "fallback": "Please consult a healthcare provider for medical advice."
                },
                confidence=0.0,
                reasoning=f"Error during inference: {str(e)}"
            )

    def _extract_patient_context(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract patient-specific context for better AI responses"""

        patient_context = {}

        # Extract relevant fields
        if "patient_id" in context:
            patient_context["patient_id"] = context["patient_id"]

        if "medical_history" in context:
            patient_context["medical_history"] = context["medical_history"]

        if "current_medications" in context:
            patient_context["current_medications"] = context["current_medications"]

        if "allergies" in context:
            patient_context["allergies"] = context["allergies"]

        if "vital_signs" in context:
            patient_context["vital_signs"] = context["vital_signs"]

        return patient_context if patient_context else None


# === COMPARISON ===

# OLD IMPLEMENTATION (Stub):
"""
async def process(self, request: AgentRequest) -> AgentResponse:
    query = request.message

    # Generate rule-based stub response
    stub_response = self._generate_stub_response(query)

    return AgentResponse(
        agent_name=self.name,
        success=True,
        data={"response": stub_response},
        confidence=0.7,
        reasoning="Rule-based response"
    )

def _generate_stub_response(self, query: str) -> str:
    # Simple keyword matching
    if "diabetes" in query.lower():
        return "Diabetes is a chronic condition..."
    elif "blood pressure" in query.lower():
        return "High blood pressure is..."
    else:
        return "Please consult a healthcare provider..."
"""

# NEW IMPLEMENTATION (MedGemma):
"""
async def process(self, request: AgentRequest) -> AgentResponse:
    query = request.message
    context = request.context or {}

    patient_context = self._extract_patient_context(context)

    # Use MedGemma for AI-powered response
    response_data = await self.model_inference.generate_response(
        query=query,
        patient_context=patient_context,
        task_type="medical_qa"
    )

    return AgentResponse(
        agent_name=self.name,
        success=True,
        data={
            "response": response_data["analysis_summary"],
            "key_findings": response_data["key_findings"],
            "disclaimer": response_data["disclaimer"]
        },
        confidence=response_data["confidence"],
        reasoning="AI-powered medical reasoning via MedGemma"
    )
"""

# === BENEFITS ===
# 1. Real medical AI reasoning instead of keyword matching
# 2. Context-aware responses using patient history
# 3. Confidence scores from AI model
# 4. Graceful fallback to stub if model unavailable
# 5. Same AgentResponse interface (no changes to orchestrator)
# 6. Maintains offline-first architecture (model runs locally)
