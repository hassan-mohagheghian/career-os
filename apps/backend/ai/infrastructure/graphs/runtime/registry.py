"""Agent Registry — Registry Pattern for agent discovery and lifecycle.

SRP: Only manages agent registration, lookup, and metadata.
OCP: New agents register without modifying the registry.
Thread-safety: Uses a lock for concurrent access.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class AgentMetadata:
    """Value object — immutable agent registration metadata."""
    name: str
    description: str = ""
    version: str = "0.1.0"
    tags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    """Singleton registry for agent instances.

    Pattern: Registry + Singleton
    - Agents register by name
    - Agents are retrieved by name
    - Metadata is stored alongside each agent
    - Thread-safe for concurrent registration
    """

    _instance: Optional[AgentRegistry] = None
    _lock_class = threading.Lock()

    def __init__(self):
        self._agents: dict[str, Any] = {}
        self._metadata: dict[str, AgentMetadata] = {}
        self._lock = threading.Lock()

    @classmethod
    def instance(cls) -> AgentRegistry:
        """Singleton access."""
        if cls._instance is None:
            with cls._lock_class:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton (for testing)."""
        with cls._lock_class:
            cls._instance = None

    def register(
        self,
        name: str,
        agent: Any,
        description: str = "",
        metadata: Optional[AgentMetadata] = None,
    ) -> None:
        """Register an agent by name.

        OCP: No modification needed to add new agent types.
        """
        with self._lock:
            self._agents[name] = agent
            if metadata:
                self._metadata[name] = metadata
            elif description:
                self._metadata[name] = AgentMetadata(
                    name=name, description=description
                )

    def get(self, name: str) -> Optional[Any]:
        """Retrieve an agent by name. Returns None if not found."""
        return self._agents.get(name)

    def get_metadata(self, name: str) -> Optional[AgentMetadata]:
        """Retrieve agent metadata by name."""
        return self._metadata.get(name)

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def unregister(self, name: str) -> None:
        """Remove an agent from the registry."""
        with self._lock:
            self._agents.pop(name, None)
            self._metadata.pop(name, None)

    def reset(self) -> None:
        """Clear all registered agents."""
        with self._lock:
            self._agents.clear()
            self._metadata.clear()
