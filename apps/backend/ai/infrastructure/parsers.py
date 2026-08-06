"""Structured Output Parsers — Pydantic models for AI responses.

Every AI response should produce structured outputs.
Prefer Pydantic models and validation over free-form parsing.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class JobExtractionOutput(BaseModel):
    """Structured output for job extraction."""
    title: str = Field(description="Job title/position")
    company: str = Field(description="Company name")
    location: str = Field(default="", description="Job location")
    salary: str = Field(default="", description="Salary range")
    stack: str = Field(default="", description="Required tech stack")
    description: str = Field(default="", description="Job description")
    requirements: str = Field(default="", description="Job requirements")
    benefits: str = Field(default="", description="Benefits offered")
    url: str = Field(default="", description="Job posting URL")

    @field_validator("title", "company")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip() if v else ""


class JobScoreOutput(BaseModel):
    """Structured output for job scoring."""
    fit_score: int = Field(ge=0, le=100, description="Fit score (0-100)")
    success_score: int = Field(ge=0, le=100, description="Success score (0-100)")
    overall_score: int = Field(ge=0, le=100, description="Overall score (0-100)")
    match_level: str = Field(description="Match level: High/Medium/Low")
    key_factors: list[str] = Field(default_factory=list, description="Key match factors")
    concerns: list[str] = Field(default_factory=list, description="Potential concerns")

    @field_validator("match_level")
    @classmethod
    def validate_match_level(cls, v: str) -> str:
        valid_levels = {"High", "Medium", "Low"}
        if v not in valid_levels:
            raise ValueError(f"match_level must be one of {valid_levels}")
        return v


class JobSummaryOutput(BaseModel):
    """Structured output for job summary."""
    key_responsibilities: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    attractive_factors: list[str] = Field(default_factory=list)
    career_growth: str = Field(default="")
    culture_highlights: str = Field(default="")
    summary_text: str = Field(default="")


class SkillExtractionOutput(BaseModel):
    """Structured output for skill extraction."""
    skills: list[str] = Field(default_factory=list, description="Extracted skills")
    categories: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Skills grouped by category"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")


class ResumeGenerationOutput(BaseModel):
    """Structured output for resume generation."""
    summary: str = Field(default="", description="Professional summary")
    experience: list[dict[str, Any]] = Field(default_factory=list, description="Work experience")
    skills: list[str] = Field(default_factory=list, description="Skills section")
    education: list[dict[str, Any]] = Field(default_factory=list, description="Education")
    tailored_sections: dict[str, str] = Field(
        default_factory=dict,
        description="Tailored sections for the job"
    )


class RoadmapGenerationOutput(BaseModel):
    """Structured output for roadmap generation."""
    milestones: list[dict[str, Any]] = Field(default_factory=list, description="Career milestones")
    skills_to_develop: list[str] = Field(default_factory=list, description="Skills to develop")
    timeline: str = Field(default="", description="Estimated timeline")
    resources: list[dict[str, str]] = Field(default_factory=list, description="Learning resources")
    next_steps: list[str] = Field(default_factory=list, description="Immediate next steps")
