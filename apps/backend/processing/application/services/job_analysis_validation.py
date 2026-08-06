"""Strict schema validation for the Job Analysis LLM output.

Only output that validates against this model is accepted and persisted.
Anything else is rejected by AnalyzeNode and surfaced as a clean user-facing
error. Mirrors the JSON schema built by build_job_analysis_output_schema().
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

VALID_RECOMMENDATIONS = ("apply", "consider", "skip")
VALID_STATUSES = ("matched", "missing", "low")
VALID_COMPANY_TYPES = (
    "hiring",
    "recruiter",
    "staffing",
    "consulting",
    "outsourcing",
    "unknown",
)


def _clamp_score(value: Any) -> int:
    n = int(float(value))
    return max(0, min(100, n))


class Scores(BaseModel):
    fit: int = Field(ge=0, le=100)
    success: int = Field(ge=0, le=100)

    @field_validator("fit", "success", mode="before")
    @classmethod
    def coerce_int(cls, v: Any) -> int:
        if isinstance(v, bool):
            raise ValueError("scores must be integers")
        return _clamp_score(v)


class ScoresExplanation(BaseModel):
    fit_factors: list[str] = Field(default_factory=list)
    success_factors: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)


class Summary(BaseModel):
    summary: str = Field(default="")
    resume_fit: str = Field(default="")
    note: str = Field(default="")


class Skill(BaseModel):
    name: str = Field(min_length=1)
    category: str = Field(default="")
    level: int | None = Field(default=None, ge=0, le=5)
    status: str = Field(default="missing")
    evidence: str = Field(default="")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        value = v.strip().lower()
        if value not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return value

    @field_validator("level", mode="before")
    @classmethod
    def coerce_level(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        return max(0, min(5, int(float(v))))


class CompanyReference(BaseModel):
    """A single company mentioned in a job posting (hiring or related)."""

    name: str = Field(min_length=1)
    normalized_name: str = Field(default="")
    company_type: str = Field(default="unknown")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = Field(default="")

    @field_validator("company_type")
    @classmethod
    def validate_company_type(cls, v: Any) -> str:
        value = str(v or "unknown").strip().lower()
        if value not in VALID_COMPANY_TYPES:
            raise ValueError(f"company_type must be one of {VALID_COMPANY_TYPES}")
        return value

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> float:
        if v is None or v == "":
            return 0.0
        try:
            n = float(v)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, n))

    @field_validator("normalized_name", "reason", mode="before")
    @classmethod
    def coerce_str(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()


class Companies(BaseModel):
    """Company extraction: the hiring company plus any related (recruiting)
    companies mentioned in the posting."""

    hiring_company: CompanyReference | None = None
    related_companies: list[CompanyReference] = Field(default_factory=list)

    @field_validator("related_companies", mode="before")
    @classmethod
    def coerce_related(cls, v: Any) -> list[CompanyReference]:
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("related_companies must be a list")
        return v

    @field_validator("hiring_company", mode="before")
    @classmethod
    def coerce_hiring(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        return v


class JobAnalysisOutput(BaseModel):
    """The canonical, schema-valid analysis the LLM must return."""

    title: str | None = None
    company: str | None = None
    company_url: str | None = None
    role: str | None = None
    location: str | None = None
    salary: str | None = None
    stack: str | None = None
    visa: str | None = None
    work_types: list[str] | None = None
    employment_types: list[str] | None = None
    industry: str | None = None
    domain: str | None = None
    description: str | None = None
    companies: Companies | None = None

    scores: Scores
    scores_explanation: ScoresExplanation = Field(default_factory=ScoresExplanation)
    recommendation: str
    apply_reason: str
    summary: Summary
    skills: list[Skill]
    insights: list[str]

    @field_validator("recommendation")
    @classmethod
    def validate_recommendation(cls, v: str) -> str:
        value = v.strip().lower()
        if value not in VALID_RECOMMENDATIONS:
            raise ValueError(f"recommendation must be one of {VALID_RECOMMENDATIONS}")
        return value

    @field_validator("work_types", "employment_types", mode="before")
    @classmethod
    def coerce_string_list(cls, v: Any) -> list[str] | None:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()] or None
        if isinstance(v, list):
            items = [str(x).strip() for x in v if str(x).strip()]
            return items or None
        raise ValueError("must be a list of strings")

    @field_validator("skills", mode="before")
    @classmethod
    def coerce_skills(cls, v: Any) -> Any:
        if v is None:
            raise ValueError("skills is required")
        if not isinstance(v, list):
            raise ValueError("skills must be a list")
        for s in v:
            if not isinstance(s, dict) or not str(s.get("name") or "").strip():
                raise ValueError("each skill must have a name")
        return v

    @field_validator("insights", mode="before")
    @classmethod
    def coerce_insights(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        raise ValueError("insights must be a list of strings")

    def dump_payload(self) -> dict[str, Any]:
        """Serialized validated payload (safe to persist)."""
        return self.model_dump()
