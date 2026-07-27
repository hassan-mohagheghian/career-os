"""Common schemas used across the application."""

from pydantic import BaseModel
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""
    items: list[T]
    total: int
    page: int = 1
    per_page: int = 30
    pages: int = 0


class SuccessResponse(BaseModel):
    """Standard success response for mutations."""
    status: str = "ok"
    message: str | None = None
