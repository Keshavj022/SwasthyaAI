"""
Base agent class and data models for the orchestrator.
All specialized agents must inherit from BaseAgent.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class UserType(str, Enum):
    """User type classification"""
    PATIENT = "patient"
    CLINICIAN = "clinician"
    ADMIN = "admin"


class UrgencyLevel(str, Enum):
    """Urgency classification for triage"""
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"
    NON_URGENT = "non_urgent"


class ConfidenceLevel(str, Enum):
    """Confidence level display"""
    VERY_LOW = "very_low"  # <20%
    LOW = "low"            # 20-49%
    MODERATE = "moderate"  # 50-79%
    HIGH = "high"          # 80-100%


class AgentRequest(BaseModel):
    """
    Request object passed to agent's process() method.
    """
    user_id: str
    message: str
    session_id: Optional[str] = None
    attachments: Optional[List[str]] = []
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "patient_123",
                "message": "I have a fever and cough",
                "attachments": [],
                "context": {
                    "user_type": "patient",
                    "age": 34,
                    "session_id": "abc123"
                }
            }
        }


class AgentResponse(BaseModel):
    """
    Response object returned by agent's process() method.
    """
    success: bool
    agent_name: str
    data: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    red_flags: List[str] = Field(default_factory=list)
    requires_escalation: bool = False
    suggested_agents: List[str] = Field(default_factory=list)  # Other agents that might help
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def get_confidence_level(self) -> ConfidenceLevel:
        """Convert confidence score to display level"""
        if self.confidence >= 0.80:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.50:
            return ConfidenceLevel.MODERATE
        elif self.confidence >= 0.20:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def get_confidence_emoji(self) -> str:
        """Get emoji indicator for confidence"""
        level = self.get_confidence_level()
        emoji_map = {
            ConfidenceLevel.HIGH: "🟢",
            ConfidenceLevel.MODERATE: "🟡",
            ConfidenceLevel.LOW: "🟠",
            ConfidenceLevel.VERY_LOW: "🔴"
        }
        return emoji_map[level]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "agent_name": "triage",
                "data": {
                    "urgency": "routine",
                    "recommendation": "Schedule clinic visit"
                },
                "confidence": 0.78,
                "reasoning": "Based on symptom severity and duration",
                "red_flags": [],
                "requires_escalation": False
            }
        }


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Enforces consistent interface and behavior.
    """

    def __init__(self):
        self.name = self.__class__.__name__.replace("Agent", "").lower()
        self.enabled = True

    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Execute the agent's specialized task.

        Args:
            request: AgentRequest with user input and context

        Returns:
            AgentResponse with results, confidence, and metadata

        Raises:
            Exception: If processing fails
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of capability keywords this agent handles.

        Example:
            return ["emergency", "triage", "urgent", "symptoms"]
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Return human-readable description of agent's purpose.

        Example:
            return "Emergency triage and urgency classification"
        """
        pass

    def get_confidence_threshold(self) -> float:
        """
        Minimum confidence score to display results.
        Override in subclass if different threshold needed.
        """
        return 0.20  # Default: display anything above "very low"

    def get_name(self) -> str:
        """Return agent name"""
        return self.name

    def is_enabled(self) -> bool:
        """Check if agent is currently enabled"""
        return self.enabled

    def set_enabled(self, enabled: bool):
        """Enable or disable agent"""
        self.enabled = enabled

    def validate_request(self, request: AgentRequest) -> bool:
        """
        Validate request before processing.
        Override in subclass for custom validation.
        """
        if not request.message or len(request.message.strip()) == 0:
            return False
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' enabled={self.enabled}>"
