"""Strict schema validation for the Application Intelligence LLM outputs.

Only output that validates against these models is accepted and persisted.
Anything else is rejected by the GenerateNode and surfaced as a clean
user-facing error. Mirrors the JSON schemas built by
``application_intelligence_prompts``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class DocumentOutput(BaseModel):
    """The canonical, schema-valid document the LLM must return."""

    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def coerce_content(cls, v: Any) -> str:
        value = str(v or "").strip()
        if not value:
            raise ValueError("content must be a non-empty string")
        return value

    def dump_payload(self) -> dict[str, Any]:
        return {"content": self.content}
