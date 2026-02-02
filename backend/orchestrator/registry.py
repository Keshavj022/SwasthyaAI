"""
Agent Registry - Centralized catalog of all available agents.
"""

from typing import Dict, List, Optional
from orchestrator.base import BaseAgent
import logging

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Singleton registry for managing all agents.
    Provides lookup by name or capability.
    """

    _instance = None
    _agents: Dict[str, BaseAgent] = {}

    def __new__(cls):
        """Singleton pattern - only one registry instance"""
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
            cls._agents = {}
        return cls._instance

    def register(self, agent: BaseAgent):
        """
        Register an agent in the registry.

        Args:
            agent: Instance of BaseAgent subclass

        Raises:
            ValueError: If agent with same name already registered
        """
        agent_name = agent.get_name()

        if agent_name in self._agents:
            logger.warning(f"Agent '{agent_name}' already registered. Overwriting.")

        self._agents[agent_name] = agent
        logger.info(f"✓ Registered agent: {agent_name}")

    def unregister(self, agent_name: str):
        """
        Unregister an agent from the registry.

        Args:
            agent_name: Name of agent to remove
        """
        if agent_name in self._agents:
            del self._agents[agent_name]
            logger.info(f"✗ Unregistered agent: {agent_name}")

    def get(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get agent by name.

        Args:
            agent_name: Name of agent to retrieve

        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(agent_name)

    def get_by_capability(self, capability: str) -> List[BaseAgent]:
        """
        Find all agents that handle a specific capability.

        Args:
            capability: Capability keyword (e.g., "emergency", "diagnosis")

        Returns:
            List of agents that handle this capability
        """
        matching_agents = []
        capability_lower = capability.lower()

        for agent in self._agents.values():
            if not agent.is_enabled():
                continue

            agent_capabilities = [cap.lower() for cap in agent.get_capabilities()]
            if capability_lower in agent_capabilities:
                matching_agents.append(agent)

        return matching_agents

    def list_all(self) -> List[BaseAgent]:
        """
        Get list of all registered agents.

        Returns:
            List of all agent instances
        """
        return list(self._agents.values())

    def list_enabled(self) -> List[BaseAgent]:
        """
        Get list of all enabled agents.

        Returns:
            List of enabled agent instances
        """
        return [agent for agent in self._agents.values() if agent.is_enabled()]

    def get_agent_info(self) -> List[Dict]:
        """
        Get metadata for all agents.

        Returns:
            List of dicts with agent information
        """
        return [
            {
                "name": agent.get_name(),
                "description": agent.get_description(),
                "capabilities": agent.get_capabilities(),
                "enabled": agent.is_enabled(),
                "confidence_threshold": agent.get_confidence_threshold()
            }
            for agent in self._agents.values()
        ]

    def clear(self):
        """Clear all registered agents (useful for testing)"""
        self._agents.clear()
        logger.info("Cleared agent registry")

    def __len__(self) -> int:
        """Return number of registered agents"""
        return len(self._agents)

    def __repr__(self) -> str:
        return f"<AgentRegistry agents={len(self._agents)}>"


# Global singleton instance
registry = AgentRegistry()
