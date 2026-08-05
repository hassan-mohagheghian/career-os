"""Company repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ICompanyRepository(ABC):
    """Interface for company data access."""

    @abstractmethod
    def list_all(self) -> list[dict[str, Any]]:
        """List all companies."""
        ...

    @abstractmethod
    def get_by_id(self, company_id: str) -> dict[str, Any] | None:
        """Get a company by ID."""
        ...

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new company."""
        ...

    @abstractmethod
    def update(self, company_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a company."""
        ...

    @abstractmethod
    def delete(self, company_id: str) -> bool:
        """Delete a company."""
        ...

    @abstractmethod
    def get_intelligence(self, company_id: str) -> dict[str, Any] | None:
        """Get company intelligence data."""
        ...

    @abstractmethod
    def list_by_status(self, status: str) -> list[dict[str, Any]]:
        """List companies by lifecycle status."""
        ...

    @abstractmethod
    def get_processing_count(self) -> int:
        """Count companies currently in processing status."""
        ...

    @abstractmethod
    def get_queued_count(self) -> int:
        """Count companies in queued status."""
        ...

    @abstractmethod
    def update_status(self, company_id: str, status: str, **extra: Any) -> bool:
        """Update company status and optional extra fields."""
        ...

    @abstractmethod
    def pick_queued_item(self) -> dict[str, Any] | None:
        """Pick the oldest queued company and claim it (set to processing). Returns item or None."""
        ...

    @abstractmethod
    def get_processing_items(self) -> list[dict[str, Any]]:
        """Get all currently processing companies."""
        ...

    @abstractmethod
    def update_fields(self, company_id: str, **fields: Any) -> bool:
        """Update arbitrary fields on a company."""
        ...
