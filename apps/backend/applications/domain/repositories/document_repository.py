"""Document repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IDocumentRepository(ABC):
    """Data access for versioned ApplicationDocument rows."""

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a document version. Returns the stored dict."""
        ...

    @abstractmethod
    def list_for_application(self, application_id: str) -> list[dict[str, Any]]:
        """List all document versions for an application, newest first."""
        ...

    @abstractmethod
    def list_by_type(self, application_id: str, document_type: str) -> list[dict[str, Any]]:
        """List document versions of one type, newest first."""
        ...

    @abstractmethod
    def get_by_id(self, document_id: str) -> dict[str, Any] | None:
        """Get a document version by id, or None."""
        ...

    @abstractmethod
    def get_next_version(self, application_id: str, document_type: str) -> int:
        """Return the next version number for a document type on an application."""
        ...

    @abstractmethod
    def update(self, document_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a document version (e.g. user edits the content)."""
        ...

    @abstractmethod
    def delete(self, document_id: str) -> bool:
        """Delete a document version. Returns True when a row was removed."""
        ...
