"""Note repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class INoteRepository(ABC):
    """Data access for ApplicationNote rows."""

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a note. Returns the stored dict."""
        ...

    @abstractmethod
    def list_for_application(self, application_id: str) -> list[dict[str, Any]]:
        """List notes for an application, newest first (created_at DESC)."""
        ...

    @abstractmethod
    def get_by_id(self, note_id: str) -> dict[str, Any] | None:
        """Get a note by id, or None."""
        ...

    @abstractmethod
    def delete(self, note_id: str) -> bool:
        """Delete a note. Returns True when a row was removed."""
        ...
