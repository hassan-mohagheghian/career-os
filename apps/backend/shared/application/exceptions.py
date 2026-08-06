"""Application exception hierarchy.

Preserves the existing AppError hierarchy while placing it
in the shared kernel for cross-context use.
"""


class AppError(Exception):
    """Base application error."""
    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None, details: dict | None = None):
        if detail:
            self.detail = detail
        self.details = details
        super().__init__(self.detail)


class NotFoundError(AppError):
    """Resource not found."""
    code: str = "NOT_FOUND"
    status_code: int = 404
    detail: str = "Resource not found"


class ValidationError(AppError):
    """Request validation failed."""
    code: str = "VALIDATION_ERROR"
    status_code: int = 422
    detail: str = "Validation failed"


class ConflictError(AppError):
    """Resource already exists."""
    code: str = "CONFLICT"
    status_code: int = 409
    detail: str = "Resource already exists"


class BadRequestError(AppError):
    """Invalid request."""
    code: str = "BAD_REQUEST"
    status_code: int = 400
    detail: str = "Bad request"


class JobAlreadyExistsError(ConflictError):
    """Job with the same URL already exists."""
    code: str = "JOB_ALREADY_EXISTS"
    detail: str = "A Job with the same primary URL already exists."

    def __init__(self, job_id: str | None = None):
        super().__init__(details={"job_id": job_id} if job_id else None)


class ExternalServiceError(AppError):
    """External API call failed."""
    code: str = "EXTERNAL_SERVICE_ERROR"
    status_code: int = 502
    detail: str = "External service error"
