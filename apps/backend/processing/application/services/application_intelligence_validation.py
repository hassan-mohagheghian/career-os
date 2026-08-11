"""Strict schema validation for the Application Intelligence LLM outputs.

Only output that validates against these models is accepted and persisted.
Anything else is rejected by the GenerateNode and surfaced as a clean
user-facing error. Mirrors the JSON schemas built by
``application_intelligence_prompts``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

VALID_GAP_LEVELS = ("missing", "low", "matching")
VALID_PRIORITIES = ("high", "medium", "low")


def _clean_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]
    return []


class HardSkillPlan(BaseModel):
    skill: str = Field(min_length=1)
    gap_level: str = "missing"
    priority: str = "medium"
    why: str = Field(default="")
    what_to_learn: list[str] = Field(default_factory=list)
    how_to_practice: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    estimated_effort: str = Field(default="")

    @field_validator("gap_level")
    @classmethod
    def validate_gap_level(cls, v: str) -> str:
        value = str(v or "missing").strip().lower()
        if value not in VALID_GAP_LEVELS:
            raise ValueError(f"gap_level must be one of {VALID_GAP_LEVELS}")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        value = str(v or "medium").strip().lower()
        if value not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}")
        return value

    @field_validator("what_to_learn", "how_to_practice", "resources", mode="before")
    @classmethod
    def coerce_lists(cls, v: Any) -> list[str]:
        return _clean_string_list(v)


class SoftSkillPlan(BaseModel):
    skill: str = Field(min_length=1)
    priority: str = "medium"
    why: str = Field(default="")
    what_to_improve: list[str] = Field(default_factory=list)
    how_to_practice: list[str] = Field(default_factory=list)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        value = str(v or "medium").strip().lower()
        if value not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}")
        return value

    @field_validator("what_to_improve", "how_to_practice", mode="before")
    @classmethod
    def coerce_lists(cls, v: Any) -> list[str]:
        return _clean_string_list(v)


class PreparationOutput(BaseModel):
    """The canonical, schema-valid preparation plan the LLM must return."""

    hard_skills: list[HardSkillPlan] = Field(default_factory=list)
    soft_skills: list[SoftSkillPlan] = Field(default_factory=list)

    @field_validator("hard_skills", mode="before")
    @classmethod
    def coerce_hard_skills(cls, v: Any) -> Any:
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("hard_skills must be a list")
        for s in v:
            if not isinstance(s, dict) or not str(s.get("skill") or "").strip():
                raise ValueError("each hard_skill must have a skill name")
        return v

    @field_validator("soft_skills", mode="before")
    @classmethod
    def coerce_soft_skills(cls, v: Any) -> Any:
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("soft_skills must be a list")
        return v

    def dump_payload(self) -> dict[str, Any]:
        return self.model_dump()


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
