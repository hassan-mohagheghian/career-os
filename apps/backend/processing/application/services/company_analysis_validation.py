"""Strict schema validation for the Company Analysis LLM output.

Only output that validates against this model is accepted and persisted.
Anything else is rejected by AnalyzeCompanyNode and surfaced as a clean
user-facing error. Combines the extraction, intelligence, recommendation and
scores sections from the legacy company_extract / company_analyze prompts into
a single canonical output.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

VALID_COMPANY_TYPES = (
    "PRODUCT_COMPANY",
    "RECRUITING_AGENCY",
    "STAFFING_COMPANY",
    "CONSULTING_COMPANY",
    "UNKNOWN",
)


def _clamp_score(value: Any) -> int:
    n = int(float(value))
    return max(0, min(100, n))


def _coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [x.strip() for x in value.split(",") if x.strip()]
        return items if items else ([value.strip()] if value.strip() else [])
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


def _coerce_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        import json
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


class CompanySkillInput(BaseModel):
    """A single skill observed at the company (name + optional detail)."""

    name: str
    category: str = Field(default="")
    evidence: str = Field(default="")

    @field_validator("name", "category", "evidence", mode="before")
    @classmethod
    def coerce_str(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()


def _coerce_skill_list(value: Any) -> list[CompanySkillInput]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [x.strip() for x in value.split(",") if x.strip()]
        value = items
    if isinstance(value, list):
        result: list[CompanySkillInput] = []
        for item in value:
            if isinstance(item, str):
                name = item.strip()
                if name:
                    result.append(CompanySkillInput(name=name))
            elif isinstance(item, dict):
                name = str(item.get("name") or "").strip()
                if name:
                    result.append(CompanySkillInput(**item))
        return result
    return []


class CompanyExtraction(BaseModel):
    """The extractable company facts (mirrors the legacy extraction schema)."""

    name: str | None = None
    website: str | None = None
    domain: str | None = None
    industry: str | None = None
    country: str | None = None
    city: str | None = None
    description: str | None = None
    company_size: str | None = None
    company_type: str | None = None
    logo_url: str | None = None
    founded_year: str | None = None
    headquarters_full: str | None = None
    countries_of_operation: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    tech_stack: dict[str, Any] = Field(default_factory=dict)
    work_environment: dict[str, Any] = Field(default_factory=dict)
    funding_stage: str | None = None
    funding_amount: str | None = None
    skills: list[CompanySkillInput] = Field(default_factory=list)

    @field_validator("company_type")
    @classmethod
    def validate_company_type(cls, v: Any) -> str | None:
        if v is None or str(v).strip() == "":
            return None
        value = str(v).strip().upper()
        if value not in VALID_COMPANY_TYPES:
            return "UNKNOWN"
        return value

    @field_validator("countries_of_operation", "products", mode="before")
    @classmethod
    def coerce_string_list(cls, v: Any) -> list[str]:
        return _coerce_string_list(v)

    @field_validator("tech_stack", "work_environment", mode="before")
    @classmethod
    def coerce_dict(cls, v: Any) -> dict[str, Any]:
        return _coerce_dict(v)

    @field_validator("skills", mode="before")
    @classmethod
    def coerce_skills(cls, v: Any) -> list[CompanySkillInput]:
        return _coerce_skill_list(v)

    @field_validator(
        "name", "website", "domain", "industry", "country", "city",
        "description", "company_size", "logo_url", "founded_year",
        "headquarters_full", "funding_stage", "funding_amount",
        mode="before",
    )
    @classmethod
    def coerce_str(cls, v: Any) -> Any:
        if v is None:
            return None
        value = str(v).strip()
        return value or None


class CompanyScores(BaseModel):
    fit: int = Field(ge=0, le=100)
    success: int = Field(ge=0, le=100)
    overall: int | None = Field(default=None, ge=0, le=100)
    fit_grade: str = Field(default="")
    overall_grade: str = Field(default="")
    fit_explanation: str = Field(default="")
    fit_positive_factors: list[str] = Field(default_factory=list)
    fit_negative_factors: list[str] = Field(default_factory=list)
    success_explanation: str = Field(default="")
    success_positive_factors: list[str] = Field(default_factory=list)
    success_negative_factors: list[str] = Field(default_factory=list)

    @field_validator("fit", "success", mode="before")
    @classmethod
    def coerce_score(cls, v: Any) -> int:
        if isinstance(v, bool):
            raise ValueError("scores must be integers")
        return _clamp_score(v)

    @field_validator("overall", mode="before")
    @classmethod
    def coerce_overall(cls, v: Any) -> int | None:
        if v is None or v == "":
            return None
        return _clamp_score(v)

    @field_validator(
        "fit_positive_factors", "fit_negative_factors",
        "success_positive_factors", "success_negative_factors",
        mode="before",
    )
    @classmethod
    def coerce_factor_list(cls, v: Any) -> list[str]:
        return _coerce_string_list(v)

    @field_validator("fit_grade", "overall_grade", "fit_explanation", "success_explanation", mode="before")
    @classmethod
    def coerce_str(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()


class CompanyIntelligence(BaseModel):
    """The deep intelligence report sections (mirrors the legacy analyze schema)."""

    overview: dict[str, Any] = Field(default_factory=dict)
    culture_analysis: dict[str, Any] = Field(default_factory=dict)
    international_analysis: dict[str, Any] = Field(default_factory=dict)
    career_analysis: dict[str, Any] = Field(default_factory=dict)
    benefits_analysis: dict[str, Any] = Field(default_factory=dict)
    visa_analysis: dict[str, Any] = Field(default_factory=dict)
    technology_analysis: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "overview", "culture_analysis", "international_analysis",
        "career_analysis", "benefits_analysis", "visa_analysis",
        "technology_analysis",
        mode="before",
    )
    @classmethod
    def coerce_dict(cls, v: Any) -> dict[str, Any]:
        return _coerce_dict(v)


class CompanyRecommendation(BaseModel):
    priority: str = Field(default="B")
    observation: str = Field(default="")
    evidence: str = Field(default="")
    impact: str = Field(default="")
    action: str = Field(default="")
    ideal_role: str = Field(default="")
    timing: str = Field(default="")

    @field_validator("priority", "observation", "evidence", "impact", "action", "ideal_role", "timing", mode="before")
    @classmethod
    def coerce_str(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()


class CompanyCombinedAnalysisOutput(BaseModel):
    """The canonical, schema-valid combined analysis the LLM must return.

    Mirrors the JSON schema built by build_company_analysis_output_schema().
    """

    extraction: CompanyExtraction
    intelligence: CompanyIntelligence = Field(default_factory=CompanyIntelligence)
    recommendation: CompanyRecommendation = Field(default_factory=CompanyRecommendation)
    scores: CompanyScores

    @field_validator("extraction", mode="before")
    @classmethod
    def coerce_extraction(cls, v: Any) -> Any:
        if v is None or not isinstance(v, dict):
            raise ValueError("extraction is required")
        return v

    @field_validator("scores", mode="before")
    @classmethod
    def coerce_scores(cls, v: Any) -> Any:
        if v is None or not isinstance(v, dict):
            raise ValueError("scores is required")
        return v

    def dump_payload(self) -> dict[str, Any]:
        """Serialized validated payload (safe to persist)."""
        return self.model_dump()
