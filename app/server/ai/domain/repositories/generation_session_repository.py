"""IGenerationSessionRepository — repository interface for generation sessions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..entities.generation_session import GenerationSession


class IGenerationSessionRepository(ABC):
    """Repository interface for generation session persistence.

    DDD: Defines the contract for data access without implementation details.
    The AI bounded context owns this interface.
    """

    @abstractmethod
    def get_by_id(self, session_id: str) -> Optional[GenerationSession]:
        """Get a generation session by ID."""
        ...

    @abstractmethod
    def save(self, session: GenerationSession) -> str:
        """Save or update a generation session. Returns the session ID."""
        ...

    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """Delete a generation session."""
        ...

    @abstractmethod
    def get_by_entity(self, entity_type: str, entity_id: str) -> list[GenerationSession]:
        """Get all sessions for a specific entity."""
        ...

    @abstractmethod
    def get_recent(self, limit: int = 10) -> list[GenerationSession]:
        """Get recent generation sessions."""
        ...
