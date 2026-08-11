"""Follow-up repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IFollowUpRepository(ABC):
    """Data access for ApplicationFollowUp rows."""

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a follow-up. Returns the stored dict."""
        ...

    @abstractmethod
    def list_for_application(self, application_id: str) -> list[dict[str, Any]]:
        """List follow-ups for an application, soonest scheduled first."""
        ...

    @abstractmethod
    def get_by_id(self, follow_up_id: str) -> dict[str, Any] | None:
        """Get a follow-up by id, or None."""
        ...

    @abstractmethod
    def update(self, follow_up_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update follow-up fields (scheduled_at, note, completed_at)."""
        ...

    @abstractmethod
    def delete(self, follow_up_id: str) -> bool:
        """Delete a follow-up. Returns True when a row was removed."""
        ...
