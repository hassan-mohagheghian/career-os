"""Company link repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ICompanyLinkRepository(ABC):
    """Interface for company link data access."""

    @abstractmethod
    def get_by_company_id(self, company_id: str) -> list[dict[str, Any]]:
        """Get all links for a company."""
        ...

    @abstractmethod
    def get_by_id(self, link_id: int) -> dict[str, Any] | None:
        """Get a link by ID."""
        ...

    @abstractmethod
    def create(self, company_id: str, url: str, title: str = "", description: str = "") -> dict[str, Any]:
        """Create a new link."""
        ...

    @abstractmethod
    def delete(self, link_id: int, company_id: str) -> bool:
        """Delete a link."""
        ...

    @abstractmethod
    def reset_statuses(self, company_id: str) -> int:
        """Reset all link statuses for a company. Returns count reset."""
        ...

    @abstractmethod
    def update_status(self, link_id: int, status: str, extracted_content: str = "") -> bool:
        """Update a link's status and extracted content."""
        ...
