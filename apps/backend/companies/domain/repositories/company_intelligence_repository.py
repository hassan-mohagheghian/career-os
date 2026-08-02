"""Company intelligence repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ICompanyIntelligenceRepository(ABC):
    """Interface for company intelligence data access."""

    @abstractmethod
    def get_by_company_id(self, company_id: int) -> dict[str, Any] | None:
        """Get intelligence data for a company."""
        ...

    @abstractmethod
    def upsert(self, company_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Insert or update company intelligence."""
        ...

    @abstractmethod
    def delete_by_company_id(self, company_id: int) -> bool:
        """Delete intelligence for a company."""
        ...
