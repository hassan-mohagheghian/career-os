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
    def get_by_id(self, company_id: int) -> dict[str, Any] | None:
        """Get a company by ID."""
        ...

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new company."""
        ...

    @abstractmethod
    def update(self, company_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a company."""
        ...

    @abstractmethod
    def delete(self, company_id: int) -> bool:
        """Delete a company."""
        ...

    @abstractmethod
    def get_intelligence(self, company_id: int) -> dict[str, Any] | None:
        """Get company intelligence data."""
        ...
