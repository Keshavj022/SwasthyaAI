"""
Agent initialization and registration.

All agents are registered here and available through the orchestrator.
"""

from orchestrator.registry import registry
from agents.triage_agent import TriageAgent
from agents.diagnostic_support_agent import DiagnosticSupportAgent
from agents.image_analysis_agent import ImageAnalysisAgent
from agents.drug_info_agent import DrugInfoAgent
from agents.communication_agent import CommunicationAgent
from agents.health_support_agent import HealthSupportAgent
from agents.health_memory_agent import HealthMemoryAgent
from agents.appointment_agent import AppointmentAgent
from agents.nearby_doctors_agent import NearbyDoctorsAgent
from agents.voice_agent import VoiceAgent
import logging

logger = logging.getLogger(__name__)


def register_all_agents():
    """
    Register all available agents with the orchestrator.
    Called during application startup.
    """
    logger.info("Registering agents...")

    # Core agents
    registry.register(TriageAgent())
    registry.register(DiagnosticSupportAgent())
    registry.register(ImageAnalysisAgent())
    registry.register(DrugInfoAgent())
    registry.register(CommunicationAgent())
    registry.register(HealthSupportAgent())
    registry.register(HealthMemoryAgent())
    registry.register(AppointmentAgent())
    registry.register(NearbyDoctorsAgent())
    registry.register(VoiceAgent())

    logger.info(f"✓ Registered {len(registry)} agents successfully")

    # Log registered agents
    for agent in registry.list_enabled():
        logger.info(f"  - {agent.get_name()}: {agent.get_description()}")


# Export agents for convenience
__all__ = [
    "TriageAgent",
    "DiagnosticSupportAgent",
    "ImageAnalysisAgent",
    "DrugInfoAgent",
    "CommunicationAgent",
    "HealthSupportAgent",
    "HealthMemoryAgent",
    "AppointmentAgent",
    "NearbyDoctorsAgent",
    "VoiceAgent",
    "register_all_agents"
]
