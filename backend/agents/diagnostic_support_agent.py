"""
Diagnostic Support Agent - Provides differential diagnosis suggestions.

Responsibilities:
- Analyze symptoms and suggest possible conditions
- Provide ranked differential diagnoses with confidence
- Highlight key features and missing information
- NEVER make definitive diagnoses

Current Implementation: Mock responses with pattern matching
Future: Integrate MedGemma for medical reasoning
"""

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
from typing import List, Dict


class DiagnosticSupportAgent(BaseAgent):
    """
    Provides differential diagnosis support based on symptoms.
    """

    def __init__(self):
        super().__init__()
        self.name = "diagnostic_support"

        # Mock knowledge base (symptom → possible conditions)
        self.symptom_patterns = {
            ("fever", "cough"): [
                {"condition": "Viral upper respiratory infection", "confidence": 0.70},
                {"condition": "Community-acquired pneumonia", "confidence": 0.60},
                {"condition": "Influenza", "confidence": 0.55}
            ],
            ("headache", "fever"): [
                {"condition": "Viral illness", "confidence": 0.65},
                {"condition": "Sinusitis", "confidence": 0.55},
                {"condition": "Meningitis (if severe/neck stiffness)", "confidence": 0.40}
            ],
            ("abdominal pain", "nausea"): [
                {"condition": "Gastroenteritis", "confidence": 0.68},
                {"condition": "Food poisoning", "confidence": 0.60},
                {"condition": "Appendicitis (if right lower quadrant)", "confidence": 0.50}
            ]
        }

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Generate differential diagnosis based on symptoms.
        """
        message = request.message.lower()

        # Extract symptoms (mock implementation)
        detected_symptoms = self._extract_symptoms(message)

        if not detected_symptoms:
            return AgentResponse(
                success=True,
                agent_name=self.name,
                data={
                    "message": "Unable to identify specific symptoms for differential diagnosis.",
                    "suggestion": "Please describe your symptoms in more detail.",
                    "helpful_info": [
                        "When did symptoms start?",
                        "How severe are they (mild/moderate/severe)?",
                        "Any associated symptoms?",
                        "Any recent exposures or travel?"
                    ]
                },
                confidence=0.30,
                reasoning="Insufficient symptom information provided",
                red_flags=[],
                requires_escalation=False
            )

        # Match symptoms to conditions
        differential = self._generate_differential(detected_symptoms)

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "detected_symptoms": detected_symptoms,
                "differential_diagnosis": differential,
                "clinical_correlation_needed": [
                    "Physical examination findings",
                    "Vital signs",
                    "Duration and progression of symptoms",
                    "Past medical history"
                ],
                "recommended_workup": [
                    "Complete history and physical examination",
                    "Consider laboratory tests if indicated",
                    "Imaging if clinically warranted"
                ],
                "note": "This is a suggested differential diagnosis only. Clinical correlation required."
            },
            confidence=0.72,
            reasoning=f"Based on symptoms: {', '.join(detected_symptoms)}",
            red_flags=[],
            requires_escalation=False
        )

    def _extract_symptoms(self, message: str) -> List[str]:
        """Extract symptoms from message (mock implementation)"""
        symptom_keywords = [
            "fever", "cough", "headache", "nausea", "vomiting",
            "diarrhea", "pain", "fatigue", "shortness of breath",
            "chest pain", "abdominal pain", "dizziness"
        ]

        detected = []
        for symptom in symptom_keywords:
            if symptom in message:
                detected.append(symptom)

        return detected

    def _generate_differential(self, symptoms: List[str]) -> List[Dict]:
        """Generate differential diagnosis based on symptoms"""

        # Try to match symptom patterns
        symptom_tuple = tuple(sorted(symptoms[:2]))  # Use first 2 symptoms

        if symptom_tuple in self.symptom_patterns:
            return self.symptom_patterns[symptom_tuple]

        # Default generic differential
        return [
            {
                "condition": "Viral illness",
                "confidence": 0.60,
                "reasoning": "Common presentation of viral infection",
                "key_features": "Matches reported symptoms",
                "missing_info": "Need physical exam and duration"
            },
            {
                "condition": "Bacterial infection",
                "confidence": 0.45,
                "reasoning": "Alternative consideration",
                "key_features": "May present similarly",
                "missing_info": "Need lab work and clinical assessment"
            },
            {
                "condition": "Other etiologies",
                "confidence": 0.30,
                "reasoning": "Multiple other causes possible",
                "key_features": "Requires clinical evaluation",
                "missing_info": "Comprehensive assessment needed"
            }
        ]

    def get_capabilities(self) -> List[str]:
        return ["diagnosis", "diagnostic", "condition", "disease", "symptoms", "what do i have"]

    def get_description(self) -> str:
        return "Differential diagnosis support based on symptoms (suggestions only, not definitive)"

    def get_confidence_threshold(self) -> float:
        return 0.50
