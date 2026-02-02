"""
Triage Agent - Emergency triage and urgency classification.

Responsibilities:
- Classify symptom urgency (emergency/urgent/routine)
- Detect red-flag conditions
- Recommend appropriate care setting
- Escalate emergencies immediately

Current Implementation: Mock responses with rule-based patterns
Future: Integrate MedGemma for advanced triage
"""

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse, UrgencyLevel
from typing import List
import re


class TriageAgent(BaseAgent):
    """
    Triages patient symptoms and determines urgency level.
    """

    def __init__(self):
        super().__init__()
        self.name = "triage"

        # Red flag patterns for emergency detection
        self.emergency_patterns = {
            "cardiac": [
                r"chest pain", r"crushing.*chest", r"heart attack",
                r"left arm.*pain", r"radiating.*pain"
            ],
            "neurological": [
                r"stroke", r"facial droop", r"slurred speech",
                r"sudden.*weakness", r"worst headache"
            ],
            "respiratory": [
                r"can't breathe", r"difficulty breathing",
                r"severe shortness.*breath", r"choking"
            ],
            "hemorrhage": [
                r"severe bleeding", r"vomiting blood", r"blood loss"
            ]
        }

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Triage patient symptoms and determine urgency.
        """
        message = request.message.lower()

        # Check for emergency red flags
        red_flags = self._check_emergency_patterns(message)

        if red_flags:
            # EMERGENCY - immediate escalation
            return AgentResponse(
                success=True,
                agent_name=self.name,
                data={
                    "urgency_level": "EMERGENCY",
                    "recommendation": "SEEK IMMEDIATE MEDICAL ATTENTION",
                    "action": "Call emergency services (911) or go to nearest ED immediately",
                    "red_flags": red_flags,
                    "next_steps": [
                        "Do not drive yourself",
                        "Call 911 for ambulance",
                        "If alone, call someone for help",
                        "Do not wait for appointment"
                    ]
                },
                confidence=0.95,
                reasoning=f"Emergency indicators detected: {', '.join(red_flags)}",
                red_flags=red_flags,
                requires_escalation=True
            )

        # Check for urgent symptoms
        if self._is_urgent(message):
            return AgentResponse(
                success=True,
                agent_name=self.name,
                data={
                    "urgency_level": "URGENT",
                    "recommendation": "Seek medical attention within 24 hours",
                    "action": "Schedule urgent care or same-day clinic visit",
                    "reasoning": "Symptoms warrant prompt evaluation but not emergency care",
                    "next_steps": [
                        "Call clinic for same-day or next-day appointment",
                        "Monitor symptoms for worsening",
                        "Seek emergency care if symptoms worsen"
                    ]
                },
                confidence=0.75,
                reasoning="Symptoms suggest need for prompt medical evaluation",
                red_flags=[],
                requires_escalation=False
            )

        # Routine/non-urgent
        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "urgency_level": "ROUTINE",
                "recommendation": "Schedule routine clinic visit",
                "action": "Book appointment within next few days",
                "reasoning": "Symptoms can be evaluated during routine visit",
                "next_steps": [
                    "Monitor symptoms",
                    "Keep symptom diary if helpful",
                    "Schedule appointment when convenient",
                    "Seek urgent care if symptoms worsen"
                ],
                "self_care": [
                    "Stay hydrated",
                    "Get adequate rest",
                    "Take over-the-counter medications as appropriate"
                ]
            },
            confidence=0.70,
            reasoning="No immediate red flags detected. Routine evaluation recommended.",
            red_flags=[],
            requires_escalation=False
        )

    def _check_emergency_patterns(self, message: str) -> List[str]:
        """Check for emergency red flag patterns"""
        detected_flags = []

        for category, patterns in self.emergency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    detected_flags.append(f"{category}: {pattern}")
                    break  # Only add category once

        return detected_flags

    def _is_urgent(self, message: str) -> bool:
        """Check if symptoms warrant urgent (not emergency) care"""
        urgent_keywords = [
            "high fever", "severe pain", "vomiting", "can't keep.*down",
            "severe.*cough", "chest tightness", "rapid.*heart"
        ]

        for keyword in urgent_keywords:
            if re.search(keyword, message, re.IGNORECASE):
                return True

        return False

    def get_capabilities(self) -> List[str]:
        return ["emergency", "urgent", "triage", "symptoms", "sick", "pain"]

    def get_description(self) -> str:
        return "Emergency triage and urgency classification based on symptoms"

    def get_confidence_threshold(self) -> float:
        return 0.60
