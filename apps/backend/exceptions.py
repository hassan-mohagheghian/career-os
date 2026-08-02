"""Custom exception classes for the application.

Re-exports from shared kernel for backward compatibility.
All new code should import from shared.application.exceptions directly.
"""

from shared.application.exceptions import (
    AppError,
    NotFoundError,
    ValidationError,
    ConflictError,
    BadRequestError,
    ExternalServiceError,
)

__all__ = [
    "AppError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "BadRequestError",
    "ExternalServiceError",
]
