"""Preparation repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IPreparationRepository(ABC):
    """Data access for versioned ApplicationPreparation rows."""

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a preparation version. Returns the stored dict."""
        ...

    @abstractmethod
    def get_latest(self, application_id: str) -> dict[str, Any] | None:
        """Get the newest preparation plan for an application, or None."""
        ...

    @abstractmethod
    def get_next_version(self, application_id: str) -> int:
        """Return the next version number for an application's preparation plan."""
        ...
