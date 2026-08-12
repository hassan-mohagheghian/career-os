"""Strict schema validation for the Roadmap Generation LLM output.

Only output that validates against these models is accepted and persisted.
Anything else is rejected by the GenerateNode and surfaced as a clean
user-facing error. Mirrors the JSON schema built by
``roadmap_generation_prompts``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

VALID_ROADMAP_PRIORITIES = ("critical", "high", "medium", "low")


def _clean_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]
    return []


def _clean_string(value: Any, default: str = "") -> str:
    return str(value or default).strip()


class TaskPlan(BaseModel):
    """A single actionable task inside a milestone."""

    title: str = Field(min_length=1)
    description: str = Field(default="")
    estimated_effort: str | None = Field(default=None)
    success_criteria: str | None = Field(default=None)

    @field_validator("title")
    @classmethod
    def coerce_title(cls, v: Any) -> str:
        value = _clean_string(v)
        if not value:
            raise ValueError("task title must be a non-empty string")
        return value

    @field_validator("description")
    @classmethod
    def coerce_description(cls, v: Any) -> str:
        return _clean_string(v)


class MilestonePlan(BaseModel):
    """An outcome-based milestone with its skills and concrete tasks."""

    title: str = Field(min_length=1)
    description: str = Field(default="")
    priority: str = "medium"
    success_criteria: str | None = Field(default=None)
    skills: list[str] = Field(default_factory=list)
    tasks: list[TaskPlan] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def coerce_title(cls, v: Any) -> str:
        value = _clean_string(v)
        if not value:
            raise ValueError("milestone title must be a non-empty string")
        return value

    @field_validator("description")
    @classmethod
    def coerce_description(cls, v: Any) -> str:
        return _clean_string(v)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Any) -> str:
        value = str(v or "medium").strip().lower()
        if value not in VALID_ROADMAP_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_ROADMAP_PRIORITIES}")
        return value

    @field_validator("skills", mode="before")
    @classmethod
    def coerce_skills(cls, v: Any) -> list[str]:
        return _clean_string_list(v)

    @field_validator("tasks", mode="before")
    @classmethod
    def coerce_tasks(cls, v: Any) -> Any:
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("tasks must be a list")
        return v

    @field_validator("tasks")
    @classmethod
    def cap_tasks(cls, v: list[TaskPlan]) -> list[TaskPlan]:
        return v[:8]


class GoalOutput(BaseModel):
    """The single JOB goal attached to the roadmap."""

    type: str = "JOB"
    title: str = Field(default="")
    description: str = Field(default="")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Any) -> str:
        value = str(v or "JOB").strip().upper()
        if value != "JOB":
            raise ValueError("goal type must be JOB")
        return value

    @field_validator("title")
    @classmethod
    def coerce_title(cls, v: Any) -> str:
        return _clean_string(v)


class RoadmapOutput(BaseModel):
    """The canonical, schema-valid roadmap the LLM must return."""

    title: str = Field(default="")
    goal: GoalOutput | None = Field(default=None)
    milestones: list[MilestonePlan] = Field(default_factory=list, validate_default=True)

    @field_validator("title")
    @classmethod
    def coerce_title(cls, v: Any) -> str:
        return _clean_string(v)

    @field_validator("milestones", mode="before")
    @classmethod
    def coerce_milestones(cls, v: Any) -> Any:
        if v is None:
            raise ValueError("milestones must be a list")
        if not isinstance(v, list):
            raise ValueError("milestones must be a list")
        return v

    @field_validator("milestones")
    @classmethod
    def cap_milestones(cls, v: list[MilestonePlan]) -> list[MilestonePlan]:
        if not v:
            raise ValueError("at least one milestone is required")
        return v[:8]

    def dump_payload(self) -> dict[str, Any]:
        return self.model_dump()