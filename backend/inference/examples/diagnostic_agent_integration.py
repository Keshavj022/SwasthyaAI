"""
Example: Diagnostic Agent Integration with MedGemma

This file shows how to integrate MedGemma into the Diagnostic Support Agent.
Replace stub differential diagnosis with real AI-powered clinical reasoning.

BEFORE: Uses _generate_stub_differential()
AFTER: Uses MedGemmaInference.generate_differential_diagnosis()
"""

from typing import Dict, Any, List
from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
from inference.medgemma import MedGemmaInference
from config import settings


class DiagnosticAgentWithAI(BaseAgent):
    """
    Diagnostic Support Agent with MedGemma Integration

    Generates differential diagnoses using Google's MedGemma model
    for real clinical reasoning and evidence-based analysis.
    """

    def __init__(self):
        super().__init__()
        self.name = "diagnostic_support"

        # Initialize MedGemma inference
        self.model_inference = MedGemmaInference(
            model_path=settings.MEDGEMMA_MODEL_PATH,
            device=settings.MODEL_DEVICE
        )

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process diagnostic support requests using MedGemma

        Args:
            request: Request containing symptoms and patient data

        Returns:
            AgentResponse with differential diagnoses
        """
        context = request.context or {}

        # Extract clinical data
        symptoms = context.get("symptoms", [])
        patient_history = context.get("patient_history", {})
        vital_signs = context.get("vital_signs", {})

        if not symptoms:
            return AgentResponse(
                agent_name=self.name,
                success=False,
                data={"error": "No symptoms provided"},
                confidence=0.0,
                reasoning="Cannot generate differential without symptoms"
            )

        try:
            # === THIS IS THE KEY CHANGE ===
            # OLD: response_data = self._generate_stub_differential(symptoms)
            # NEW: Use MedGemma for real differential diagnosis

            response_data = await self.model_inference.generate_differential_diagnosis(
                symptoms=symptoms,
                patient_history=patient_history,
                vital_signs=vital_signs
            )

            # Extract differential diagnoses
            differentials = response_data.get("differential_diagnoses", [])
            red_flags = response_data.get("red_flags", [])
            recommended_workup = response_data.get("recommended_workup", [])
            missing_info = response_data.get("missing_information", [])

            # Calculate overall confidence (average of top 3 diagnoses)
            if differentials:
                top_confidences = [d.get("confidence", 0.0) for d in differentials[:3]]
                overall_confidence = sum(top_confidences) / len(top_confidences)
            else:
                overall_confidence = 0.3

            # Check if using stub
            using_stub = response_data.get("stub_mode", False)

            # Build response
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data={
                    "differential_diagnoses": differentials,
                    "red_flags": red_flags,
                    "recommended_workup": recommended_workup,
                    "missing_information": missing_info,
                    "disclaimer": response_data.get("disclaimer", ""),
                    "model_used": "MedGemma" if not using_stub else "Stub",
                    "clinical_reasoning": self._format_reasoning(differentials)
                },
                confidence=overall_confidence,
                reasoning=f"Differential diagnosis generated using {'MedGemma AI' if not using_stub else 'rule-based logic'}"
            )

        except Exception as e:
            return AgentResponse(
                agent_name=self.name,
                success=False,
                data={
                    "error": f"Failed to generate differential: {str(e)}",
                    "fallback": "Please consult a qualified healthcare provider for diagnosis."
                },
                confidence=0.0,
                reasoning=f"Error during differential generation: {str(e)}"
            )

    def _format_reasoning(self, differentials: List[Dict[str, Any]]) -> str:
        """Format clinical reasoning for transparency"""

        if not differentials:
            return "No differentials generated"

        reasoning_parts = []

        for i, diff in enumerate(differentials[:3], 1):
            condition = diff.get("condition", "Unknown")
            confidence = diff.get("confidence", 0.0)
            supporting = diff.get("supporting_evidence", [])

            reasoning_parts.append(
                f"{i}. {condition} (confidence: {confidence:.2f})\n"
                f"   Supporting evidence: {', '.join(supporting[:3])}"
            )

        return "\n".join(reasoning_parts)


# === COMPARISON ===

# OLD IMPLEMENTATION (Stub):
"""
async def process(self, request: AgentRequest) -> AgentResponse:
    context = request.context or {}
    symptoms = context.get("symptoms", [])

    # Simple keyword matching for differential
    differentials = []

    if "fever" in symptoms and "cough" in symptoms:
        differentials.append({
            "condition": "Influenza",
            "confidence": 0.7,
            "supporting_evidence": ["fever", "cough"],
            "contradicting_evidence": []
        })

    return AgentResponse(
        agent_name=self.name,
        success=True,
        data={"differential_diagnoses": differentials},
        confidence=0.6,
        reasoning="Rule-based symptom matching"
    )
"""

# NEW IMPLEMENTATION (MedGemma):
"""
async def process(self, request: AgentRequest) -> AgentResponse:
    context = request.context or {}

    symptoms = context.get("symptoms", [])
    patient_history = context.get("patient_history", {})
    vital_signs = context.get("vital_signs", {})

    # Use MedGemma for AI-powered differential diagnosis
    response_data = await self.model_inference.generate_differential_diagnosis(
        symptoms=symptoms,
        patient_history=patient_history,
        vital_signs=vital_signs
    )

    differentials = response_data["differential_diagnoses"]

    return AgentResponse(
        agent_name=self.name,
        success=True,
        data={
            "differential_diagnoses": differentials,
            "red_flags": response_data["red_flags"],
            "recommended_workup": response_data["recommended_workup"],
            "disclaimer": response_data["disclaimer"]
        },
        confidence=sum(d["confidence"] for d in differentials[:3]) / 3,
        reasoning="AI-powered differential diagnosis via MedGemma"
    )
"""

# === BENEFITS ===
# 1. Real clinical reasoning instead of simple keyword matching
# 2. Evidence-based supporting/contradicting evidence for each diagnosis
# 3. Red flag detection for serious conditions
# 4. Recommended diagnostic workup (tests to order)
# 5. Identification of missing information needed for better diagnosis
# 6. Maintains same AgentResponse interface
# 7. Graceful fallback to stub if model unavailable
# 8. Fully offline (model runs locally)

# === EXAMPLE RESPONSE ===
"""
{
  "agent_name": "diagnostic_support",
  "success": true,
  "data": {
    "differential_diagnoses": [
      {
        "condition": "Influenza",
        "confidence": 0.82,
        "supporting_evidence": [
          "Fever 101°F",
          "Dry cough",
          "Body aches",
          "Fatigue",
          "Symptom onset 3 days ago"
        ],
        "contradicting_evidence": []
      },
      {
        "condition": "COVID-19",
        "confidence": 0.75,
        "supporting_evidence": [
          "Fever",
          "Dry cough",
          "Fatigue"
        ],
        "contradicting_evidence": [
          "No loss of taste/smell mentioned"
        ]
      },
      {
        "condition": "Common Cold",
        "confidence": 0.45,
        "supporting_evidence": [
          "Cough",
          "Fatigue"
        ],
        "contradicting_evidence": [
          "Fever uncommon in colds",
          "Significant body aches"
        ]
      }
    ],
    "red_flags": [],
    "recommended_workup": [
      "Rapid influenza test",
      "COVID-19 PCR or antigen test",
      "Complete blood count if symptoms worsen"
    ],
    "missing_information": [
      "Exposure history",
      "Vaccination status (flu/COVID)",
      "Duration of each symptom",
      "Presence of nasal congestion or sore throat"
    ],
    "disclaimer": "This is clinical decision support only. Consult a healthcare provider.",
    "model_used": "MedGemma"
  },
  "confidence": 0.67,
  "reasoning": "AI-powered differential diagnosis via MedGemma"
}
"""
