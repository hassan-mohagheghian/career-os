"""Candidate source repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ICandidateSourceRepository(ABC):
    """Data access for candidate profile sources (resume, linkedin, ...)."""

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a source row. Returns the stored dict."""
        ...

    @abstractmethod
    def list_for_profile(self, profile_id: str) -> list[dict[str, Any]]:
        """List sources for a profile, newest first."""
        ...

    @abstractmethod
    def get_by_type_and_version(self, profile_id: str, source_type: str, version: int) -> dict[str, Any] | None:
        """Get a specific source version for a profile, or None."""
        ...

    @abstractmethod
    def update(self, source_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update source fields (status, error, processed_at, version)."""
        ...

    @abstractmethod
    def get_latest_by_type(self, profile_id: str, source_type: str) -> dict[str, Any] | None:
        """Get the latest (highest-version) source row of a type, or None."""
        ...

    @abstractmethod
    def get_next_version(self, profile_id: str, source_type: str) -> int:
        """Return the next version number for a source type on a profile."""
        ...
