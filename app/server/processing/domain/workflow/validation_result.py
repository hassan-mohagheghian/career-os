"""ContextValidationResult — outcome of the ValidateContextNode."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContextValidationResult(BaseModel):
    valid: bool
    reasons: list[str] = Field(default_factory=list)
