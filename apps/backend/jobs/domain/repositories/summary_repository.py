"""Summary repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ISummaryRepository(ABC):
    """Interface for job summary data access."""

    @abstractmethod
    def get_by_job_id(self, job_id: str) -> dict[str, Any] | None:
        """Get a summary by job id."""
        ...

    @abstractmethod
    def get_all(self) -> list[dict[str, Any]]:
        """Get all summaries ordered by grade."""
        ...

    @abstractmethod
    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert or update a summary."""
        ...

    @abstractmethod
    def delete_by_num(self, job_id: str) -> bool:
        """Delete a summary by job id."""
        ...

    @abstractmethod
    def delete_all(self) -> int:
        """Delete all summaries. Returns count deleted."""
        ...
