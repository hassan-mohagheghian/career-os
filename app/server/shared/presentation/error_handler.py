"""Shared error handler for FastAPI exception responses."""

from fastapi import Request
from fastapi.responses import JSONResponse


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert AppError to JSON response."""
    from shared.application.exceptions import AppError
    if not isinstance(exc, AppError):
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.detail,
                "details": getattr(exc, "details", None),
            }
        },
    )
