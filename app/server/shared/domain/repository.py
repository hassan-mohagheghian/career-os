"""Base Repository interface.

All repository interfaces (ABCs) for bounded contexts should inherit from this.
Repository interfaces define data access contracts without implementation details.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class RepositoryInterface(ABC, Generic[T]):
    """Base repository interface.

    Defines the contract for data access implementations.
    Each bounded context defines its own specific repository interface
    inheriting from this base.
    """

    @abstractmethod
    def get_by_id(self, entity_id: Any) -> T | None:
        """Get an entity by its identifier."""
        ...

    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """Delete an entity by its identifier."""
        ...
