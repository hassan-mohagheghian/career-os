"""Pending job repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IPendingRepository(ABC):
    """Interface for pending job data access."""

    @abstractmethod
    def list_pending(self, table: str = "pending_jobs") -> list[dict[str, Any]]:
        """List pending items."""
        ...

    @abstractmethod
    def get_by_id(self, item_id: str, table: str = "pending_jobs") -> dict[str, Any] | None:
        """Get a pending item by ID."""
        ...

    @abstractmethod
    def create(self, data: dict[str, Any], table: str = "pending_jobs") -> dict[str, Any]:
        """Create a new pending item."""
        ...

    @abstractmethod
    def update_status(self, item_id: str, status: str, table: str = "pending_jobs") -> bool:
        """Update pending item status."""
        ...

    @abstractmethod
    def count_pending(self, table: str = "pending_jobs") -> int:
        """Count pending items."""
        ...
