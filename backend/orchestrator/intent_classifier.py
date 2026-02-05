"""
Intent Classifier - Determines which agent(s) should handle a request.

Current Implementation: Keyword-based pattern matching
Future: ML-based classification or LLM routing
"""

from typing import List, Dict, Tuple
from orchestrator.base import AgentRequest, UrgencyLevel
import re
import logging

logger = logging.getLogger(__name__)


class IntentClassification:
    """Result of intent classification"""

    def __init__(
        self,
        primary_agent: str,
        secondary_agents: List[str] = None,
        urgency: UrgencyLevel = UrgencyLevel.ROUTINE,
        confidence: float = 0.0,
        reasoning: str = ""
    ):
        self.primary_agent = primary_agent
        self.secondary_agents = secondary_agents or []
        self.urgency = urgency
        self.confidence = confidence
        self.reasoning = reasoning

    def to_dict(self) -> Dict:
        return {
            "primary_agent": self.primary_agent,
            "secondary_agents": self.secondary_agents,
            "urgency": self.urgency.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }

    def __repr__(self) -> str:
        return f"<IntentClassification primary='{self.primary_agent}' urgency={self.urgency.value} confidence={self.confidence:.2f}>"


class IntentClassifier:
    """
    Analyzes user input and determines which agent(s) to invoke.
    """

    def __init__(self):
        # Emergency keywords (highest priority)
        self.emergency_patterns = [
            r"\b(emergency|urgent|critical|severe)\b",
            r"\b(chest pain|heart attack|stroke|seizure)\b",
            r"\b(can't breathe|difficulty breathing|choking)\b",
            r"\b(unconscious|unresponsive|passed out)\b",
            r"\b(severe bleeding|hemorrhage)\b",
            r"\b(suicide|kill myself|self harm)\b",
        ]

        # Agent capability patterns (keyword → agent mapping)
        self.agent_patterns = {
            "triage": [
                r"\b(emergency|urgent|pain|symptoms|sick|ill|feeling)\b",
                r"\b(fever|cough|headache|nausea|vomiting|diarrhea|sore throat)\b",
                r"\b(how serious|should i worry|need doctor)\b",
                r"\b(i have|i'm feeling|i feel|experiencing)\b",
            ],
            "health_support": [
                r"\b(hello|hi|hey|greeting)\b",
                r"\b(daily|check in|wellness|how am i)\b",
            ],
            "diagnostic_support": [
                r"\b(diagnos\w*|condition|disease|what do i have)\b",
                r"\b(differential|possible conditions|could it be)\b",
                r"\b(symptoms suggest|indicate|might mean)\b",
            ],
            "image_analysis": [
                r"\b(x-?ray|xray|scan|ct|mri|ultrasound|imaging)\b",
                r"\b(analyze image|check image|look at|review image)\b",
                r"\b(chest x-?ray|brain scan|dermatology)\b",
            ],
            "drug_info": [
                r"\b(medication|medicine|drug|prescription|pill)\b",
                r"\b(side effect|interaction|contraindication)\b",
                r"\b(dosage|how much|how often|when to take)\b",
                r"\b(aspirin|ibuprofen|tylenol|antibiotic)\b",
            ],
            "communication": [
                r"\b(explain|what is|tell me about|describe)\b",
                r"\b(in simple terms|layman|easy to understand)\b",
                r"\b(mean\s|definition|understand)\b",
            ],
            "appointment": [
                r"\b(appointment|schedule|book|availability|available)\b",
                r"\b(see doctor|visit|consultation)\b",
                r"\b(next available|earliest|when can i)\b",
            ],
            "referral": [
                r"\b(specialist|referral|find doctor|recommend doctor)\b",
                r"\b(cardiologist|dermatologist|neurologist|oncologist)\b",
                r"\b(nearby|near me|in my area)\b",
            ],
            "health_memory": [
                r"\b(history|past|previous|records|medical record)\b",
                r"\b(last time|before|earlier|previously)\b",
                r"\b(retrieve|look up|find|search)\b",
            ],
            "document_vault": [
                r"\b(upload|store|save|document|file|report)\b",
                r"\b(lab results|test results|prescription|scan)\b",
            ],
            "voice": [
                r"\b(transcribe|voice|speech|audio|recording)\b",
                r"\b(dictate|hands-free)\b",
            ],
        }

    def classify(self, request: AgentRequest) -> IntentClassification:
        """
        Classify intent and determine which agent(s) to invoke.

        Args:
            request: AgentRequest with user message

        Returns:
            IntentClassification with primary agent, urgency, confidence
        """
        message = request.message.lower()

        # Step 1: Check for emergency patterns (highest priority)
        urgency, emergency_confidence = self._check_emergency(message)

        if urgency == UrgencyLevel.EMERGENCY:
            return IntentClassification(
                primary_agent="triage",
                secondary_agents=[],
                urgency=UrgencyLevel.EMERGENCY,
                confidence=emergency_confidence,
                reasoning="Emergency keywords detected. Immediate triage required."
            )

        # Step 2: Score all agents based on keyword matches
        agent_scores = self._score_agents(message)

        if not agent_scores:
            # No matches - default to communication agent
            return IntentClassification(
                primary_agent="communication",
                secondary_agents=[],
                urgency=UrgencyLevel.ROUTINE,
                confidence=0.30,
                reasoning="No specific agent matched. Defaulting to general communication."
            )

        # Step 3: Select primary and secondary agents
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        primary_agent, primary_score = sorted_agents[0]

        # Secondary agents: any with score > 0.3 and not primary
        secondary_agents = [
            agent for agent, score in sorted_agents[1:]
            if score > 0.3
        ]

        # Adjust urgency based on triage score
        if primary_agent == "triage" and primary_score > 0.6:
            urgency = UrgencyLevel.URGENT
        elif "emergency" in message or "urgent" in message:
            urgency = UrgencyLevel.URGENT

        return IntentClassification(
            primary_agent=primary_agent,
            secondary_agents=secondary_agents[:2],  # Max 2 secondary
            urgency=urgency,
            confidence=primary_score,
            reasoning=f"Matched agent '{primary_agent}' based on keyword patterns."
        )

    def _check_emergency(self, message: str) -> Tuple[UrgencyLevel, float]:
        """
        Check if message contains emergency keywords.

        Returns:
            (urgency_level, confidence)
        """
        match_count = 0
        total_patterns = len(self.emergency_patterns)

        for pattern in self.emergency_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                match_count += 1

        if match_count > 0:
            confidence = min(0.95, 0.7 + (match_count * 0.15))
            return UrgencyLevel.EMERGENCY, confidence

        return UrgencyLevel.ROUTINE, 0.0

    def _score_agents(self, message: str) -> Dict[str, float]:
        """
        Score each agent based on keyword pattern matches.

        Returns:
            Dict of {agent_name: score} where score is 0.0-1.0
        """
        scores = {}

        for agent_name, patterns in self.agent_patterns.items():
            match_count = 0
            total_patterns = len(patterns)

            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    match_count += 1

            if match_count > 0:
                # Score based on percentage of patterns matched
                base_score = match_count / total_patterns
                # Boost score slightly for multiple matches
                boosted_score = min(0.95, base_score + (match_count * 0.1))
                scores[agent_name] = boosted_score

        return scores

    def classify_batch(self, requests: List[AgentRequest]) -> List[IntentClassification]:
        """
        Classify multiple requests in batch.

        Args:
            requests: List of AgentRequest objects

        Returns:
            List of IntentClassification results
        """
        return [self.classify(request) for request in requests]


# Global singleton instance
classifier = IntentClassifier()
