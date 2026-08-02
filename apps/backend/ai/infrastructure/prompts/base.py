from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PromptType(str, Enum):
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    TOOL = "tool"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    REPAIR = "repair"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    EVALUATION = "evaluation"
    REFLECTION = "reflection"


class PromptVersion(BaseModel):
    version: str = Field(description="Semantic version string (e.g. 1.0.0)")
    description: str = Field(default="", description="What changed in this version")
    date: str = Field(default_factory=_utc_now)


class PromptSpec(BaseModel):
    identifier: str = Field(description="Unique prompt identifier (e.g. job.extract)")
    version: str = Field(default="1.0.0", description="Current version")
    description: str = Field(default="", description="Human-readable description")
    owner: str = Field(description="Bounded context that owns this prompt")
    prompt_type: PromptType = Field(default=PromptType.SYSTEM)
    supported_providers: list[str] = Field(default_factory=lambda: ["any"])
    tags: list[str] = Field(default_factory=list)
    changelog: list[PromptVersion] = Field(default_factory=list)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utc_now)
    updated_at: str = Field(default_factory=_utc_now)
