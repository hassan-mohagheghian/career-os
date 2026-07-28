"""Base DTO and common DTO types for data transfer between layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DTO:
    """Base Data Transfer Object.

    DTOs carry data between application layer and presentation layer.
    They are simple data containers without business logic.
    """
    pass


@dataclass
class PaginationDTO(DTO):
    """Pagination parameters for list queries."""
    offset: int = 0
    limit: int = 50
    sort_by: str = "created_at"
    sort_dir: str = "desc"


@dataclass
class PaginatedResultDTO(DTO):
    """Paginated result wrapper."""
    items: list[Any] = field(default_factory=list)
    total: int = 0
    offset: int = 0
    limit: int = 50
