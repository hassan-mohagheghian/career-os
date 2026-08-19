"""Status-event (timeline) repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IStatusEventRepository(ABC):
    """Data access for ApplicationStatusEvent rows."""

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a status event. Returns the stored dict."""
        ...

    @abstractmethod
    def list_for_application(self, application_id: str) -> list[dict[str, Any]]:
        """List status events for an application, earliest changed first."""
        ...

    @abstractmethod
    def get_by_id(self, event_id: str) -> dict[str, Any] | None:
        """Get a status event by id, or None."""
        ...

    @abstractmethod
    def update(self, event_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update status event fields (changed_at)."""
        ...

    @abstractmethod
    def delete(self, event_id: str) -> bool:
        """Delete a status event. Returns True when a row was removed."""
        ...