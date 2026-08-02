"""Scoring rules schemas for request/response validation."""

from pydantic import BaseModel
from typing import Any


class RulesResponse(BaseModel):
    rules: list[dict[str, Any]]
    updated_at: str | None = None


class RulesUpdate(BaseModel):
    rules: list[dict[str, Any]]
