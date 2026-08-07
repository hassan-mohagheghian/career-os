"""Candidate repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ICandidateRepository(ABC):
    """Data access for the candidate (singleton person row)."""

    @abstractmethod
    def get_candidate(self) -> dict[str, Any] | None:
        """Get the candidate, or None if none exists yet."""
        ...

    @abstractmethod
    def create_candidate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create the candidate row. Returns the stored dict."""
        ...

    @abstractmethod
    def update_candidate(self, candidate_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update candidate core fields. Returns the updated dict or None."""
        ...
