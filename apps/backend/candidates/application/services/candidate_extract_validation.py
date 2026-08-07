"""Strict schema validation for the candidate.extract LLM output.

Only output that validates against this model is accepted and persisted.
Anything else is rejected by CandidateExtractService and surfaced as a clean
error. Mirrors the JSON schema built by build_candidate_extract_output_schema().
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

PROFICIENCY_VALUES = ("basic", "conversational", "professional", "fluent", "native")


def _coerce_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _clamp_confidence(value: Any) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, n))


def _clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, n))


def _coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


class ExtractedProfile(BaseModel):
    name: str = Field(default="")
    title: str = Field(default="")
    headline: str = Field(default="")
    summary: str = Field(default="")
    location: str = Field(default="")

    @field_validator("name", "title", "headline", "summary", "location", mode="before")
    @classmethod
    def coerce_strings(cls, v: Any) -> str:
        return _coerce_str(v)


class ExtractedSkill(BaseModel):
    name: str = Field(default="")
    level: int = Field(default=1, ge=0, le=5)
    category: str = Field(default="")
    years_of_experience: float | None = None
    last_used: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("name", "category", mode="before")
    @classmethod
    def coerce_strings(cls, v: Any) -> str:
        return _coerce_str(v)

    @field_validator("last_used", mode="before")
    @classmethod
    def coerce_optional_strings(cls, v: Any) -> str | None:
        if v is None or v == "":
            return None
        return str(v).strip()

    @field_validator("level", mode="before")
    @classmethod
    def coerce_level(cls, v: Any) -> int:
        return _clamp_int(v, 1, 0, 5)

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> float:
        return _clamp_confidence(v)

    @field_validator("years_of_experience", mode="before")
    @classmethod
    def coerce_optional_float(cls, v: Any) -> float | None:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None


class ExtractedExperience(BaseModel):
    company: str = Field(default="")
    role: str = Field(default="")
    start_date: str | None = None
    end_date: str | None = None
    duration_months: int | None = None
    summary: str = Field(default="")
    highlights: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("company", "role", "summary", mode="before")
    @classmethod
    def coerce_strings(cls, v: Any) -> str:
        return _coerce_str(v)

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def coerce_optional_strings(cls, v: Any) -> str | None:
        if v is None or v == "":
            return None
        return str(v).strip()

    @field_validator("duration_months", mode="before")
    @classmethod
    def coerce_optional_int(cls, v: Any) -> int | None:
        if v is None or v == "":
            return None
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None

    @field_validator("highlights", "skills", mode="before")
    @classmethod
    def coerce_lists(cls, v: Any) -> list[str]:
        return _coerce_str_list(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> float:
        return _clamp_confidence(v)


class ExtractedProject(BaseModel):
    name: str = Field(default="")
    description: str = Field(default="")
    url: str = Field(default="")
    role: str = Field(default="")
    skills: list[str] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("name", "description", "url", "role", mode="before")
    @classmethod
    def coerce_strings(cls, v: Any) -> str:
        return _coerce_str(v)

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def coerce_optional_strings(cls, v: Any) -> str | None:
        if v is None or v == "":
            return None
        return str(v).strip()

    @field_validator("skills", mode="before")
    @classmethod
    def coerce_lists(cls, v: Any) -> list[str]:
        return _coerce_str_list(v)

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> float:
        return _clamp_confidence(v)


class ExtractedEducation(BaseModel):
    institution: str = Field(default="")
    degree: str = Field(default="")
    field: str = Field(default="")
    start_date: str | None = None
    end_date: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("institution", "degree", "field", mode="before")
    @classmethod
    def coerce_strings(cls, v: Any) -> str:
        return _coerce_str(v)

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def coerce_optional_strings(cls, v: Any) -> str | None:
        if v is None or v == "":
            return None
        return str(v).strip()

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> float:
        return _clamp_confidence(v)


class ExtractedCertificate(BaseModel):
    name: str = Field(default="")
    issuer: str = Field(default="")
    issue_date: str | None = None
    credential_url: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("name", "issuer", "credential_url", mode="before")
    @classmethod
    def coerce_strings(cls, v: Any) -> str:
        return _coerce_str(v)

    @field_validator("issue_date", mode="before")
    @classmethod
    def coerce_optional_strings(cls, v: Any) -> str | None:
        if v is None or v == "":
            return None
        return str(v).strip()

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> float:
        return _clamp_confidence(v)


class ExtractedInterest(BaseModel):
    name: str = Field(default="")

    @field_validator("name", mode="before")
    @classmethod
    def coerce_string(cls, v: Any) -> str:
        return _coerce_str(v)


class ExtractedLanguage(BaseModel):
    name: str = Field(default="")
    proficiency: str = Field(default="")

    @field_validator("name", mode="before")
    @classmethod
    def coerce_string(cls, v: Any) -> str:
        return _coerce_str(v)

    @field_validator("proficiency", mode="before")
    @classmethod
    def coerce_proficiency(cls, v: Any) -> str:
        value = _coerce_str(v).lower()
        return value if value in PROFICIENCY_VALUES else ""


class CandidateExtractOutput(BaseModel):
    """The canonical, schema-valid extraction the LLM must return."""

    profile: ExtractedProfile = Field(default_factory=ExtractedProfile)
    skills: list[ExtractedSkill] = Field(default_factory=list)
    experiences: list[ExtractedExperience] = Field(default_factory=list)
    projects: list[ExtractedProject] = Field(default_factory=list)
    educations: list[ExtractedEducation] = Field(default_factory=list)
    certificates: list[ExtractedCertificate] = Field(default_factory=list)
    interests: list[ExtractedInterest] = Field(default_factory=list)
    languages: list[ExtractedLanguage] = Field(default_factory=list)

    @field_validator("profile", mode="before")
    @classmethod
    def coerce_profile(cls, v: Any) -> Any:
        if v is None or v == "":
            return {}
        if not isinstance(v, dict):
            return {}
        return v

    @field_validator("skills", mode="before")
    @classmethod
    def coerce_skills(cls, v: Any) -> list[dict[str, Any]]:
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("skills must be a list")
        cleaned = []
        for item in v:
            if not isinstance(item, dict):
                continue
            if not str(item.get("name") or "").strip():
                continue
            cleaned.append(item)
        return cleaned

    @field_validator("experiences", "projects", "educations", "certificates", "interests", "languages", mode="before")
    @classmethod
    def coerce_section_lists(cls, v: Any) -> Any:
        if not isinstance(v, list):
            raise ValueError("section must be a list")
        return v

    def dump_payload(self) -> dict[str, Any]:
        """Serialized validated payload (safe to persist)."""
        return self.model_dump()
