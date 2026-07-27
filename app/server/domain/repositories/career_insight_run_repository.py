"""Career insight run repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ICareerInsightRunRepository(ABC):
    """Interface for career insight run tracking."""

    @abstractmethod
    def create(self, insight_type: str, version: int = 1, status: str = "pending", session_id: str | None = None) -> dict[str, Any]:
        """Create a new insight run."""
        ...

    @abstractmethod
    def complete(self, run_id: int, status: str, error_message: str | None = None, session_id: str | None = None) -> bool:
        """Mark a run as completed."""
        ...

    @abstractmethod
    def update_session_id(self, run_id: int, session_id: str) -> bool:
        """Update session_id on a run."""
        ...

    @abstractmethod
    def get_latest_processing(self, insight_type: str | None = None) -> dict[str, Any] | None:
        """Get the latest processing run."""
        ...

    @abstractmethod
    def cleanup_stale_runs(self, cutoff: str) -> int:
        """Mark stale processing runs as failed. Returns count updated."""
        ...

    @abstractmethod
    def cancel_stale_run(self, insight_type: str) -> bool:
        """Cancel a stale processing run."""
        ...

    @abstractmethod
    def get_runs(self, insight_type: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """Get runs with optional filter."""
        ...

    @abstractmethod
    def get_total_count(self, insight_type: str | None = None) -> int:
        """Count runs with optional filter."""
        ...

    @abstractmethod
    def get_latest_session_id(self, insight_type: str) -> str | None:
        """Get the session_id of the latest run for retry."""
        ...
