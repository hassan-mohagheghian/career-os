"""Agent State — the domain model flowing through workflow graphs.

Uses Pydantic BaseModel for strongly typed state that flows through
LangGraph StateGraph nodes. Each graph can extend BaseState with
additional typed fields.

DDD Value Object: State carries all context between graph nodes.
Immutable contract: nodes return new/updated state, never modify in-place.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict

from pydantic import BaseModel, Field


class BaseState(TypedDict, total=False):
    """Typed state dictionary for agent graph execution.

    Attributes:
        input: The original user input / prompt.
        output: The final output after graph execution.
        context: Shared context (provider, config, DB connections).
        errors: List of error messages encountered during execution.
        metadata: Arbitrary metadata (duration, token counts, etc.).
        node_history: List of node names that have executed.
    """
    input: str
    output: str
    context: dict[str, Any]
    errors: list[str]
    metadata: dict[str, Any]
    node_history: list[str]


def create_initial_state(
    input: str = "",
    context: dict[str, Any] | None = None,
) -> BaseState:
    """Factory function — creates a fresh state for graph execution.

    DDD Factory: Encapsulates state creation logic.
    """
    return BaseState(
        input=input,
        output="",
        context=context or {},
        errors=[],
        metadata={},
        node_history=[],
    )


# ── Structured Output Models ────────────────────────────────────────

class JobExtractionOutput(BaseModel):
    """Structured output from job extraction graph."""
    title: str = ""
    company: str = ""
    location: str = ""
    salary: str = ""
    stack: str = ""
    description: str = ""
    requirements: str = ""
    benefits: str = ""
    url: str = ""


class JobAnalysisOutput(BaseModel):
    """Structured output from job analysis graph."""
    extraction: JobExtractionOutput = Field(default_factory=JobExtractionOutput)
    tech_stack: list[str] = Field(default_factory=list)
    requirements_analysis: dict[str, Any] = Field(default_factory=dict)
    score: str = ""
    fit_score: Optional[float] = None
    success_score: Optional[float] = None
    overall_score: Optional[float] = None
    summary: str = ""


class CompanyExtractionOutput(BaseModel):
    """Structured output from company extraction graph."""
    name: str = ""
    company_type: str = ""
    industry: str = ""
    size: str = ""
    location: str = ""
    website: str = ""
    description: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    visa_sponsorship: Optional[bool] = None


class CompanyAnalysisOutput(BaseModel):
    """Structured output from company analysis graph."""
    extraction: CompanyExtractionOutput = Field(default_factory=CompanyExtractionOutput)
    scores: dict[str, Any] = Field(default_factory=dict)
    intelligence: dict[str, Any] = Field(default_factory=dict)
    rules: dict[str, Any] = Field(default_factory=dict)


class ResumeOutput(BaseModel):
    """Structured output from resume generation graph."""
    resume_text: str = ""
    tailored_sections: list[dict[str, Any]] = Field(default_factory=list)
    match_score: Optional[float] = None
    suggestions: list[str] = Field(default_factory=list)


class CoverLetterOutput(BaseModel):
    """Structured output from cover letter generation graph."""
    cover_letter: str = ""
    paragraphs: list[str] = Field(default_factory=list)
    tone: str = "professional"
    key_highlights: list[str] = Field(default_factory=list)


class SkillExtractionOutput(BaseModel):
    """Structured output from skill extraction graph."""
    skills: list[dict[str, Any]] = Field(default_factory=list)
    categories: dict[str, list[str]] = Field(default_factory=dict)
    raw_skills: list[str] = Field(default_factory=list)


class SkillRoadmapOutput(BaseModel):
    """Structured output from skill roadmap generation graph."""
    roadmap: list[dict[str, Any]] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    estimated_timelines: dict[str, str] = Field(default_factory=dict)
    learning_resources: list[dict[str, Any]] = Field(default_factory=list)


class InsightSectionOutput(BaseModel):
    """Structured output for a single insight section."""
    section: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    recommendations: list[str] = Field(default_factory=list)


class CareerInsightsOutput(BaseModel):
    """Structured output from career insights graph."""
    overview: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    skills: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    market: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    companies: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    networking: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    opportunities: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    health_score: Optional[float] = None
    generated_sections: list[str] = Field(default_factory=list)
