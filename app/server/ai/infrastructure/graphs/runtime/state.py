from __future__ import annotations

from typing import Any, Optional, TypedDict

from pydantic import BaseModel, Field


class BaseState(TypedDict, total=False):
    input: str
    output: str
    context: dict[str, Any]
    errors: list[str]
    metadata: dict[str, Any]
    node_history: list[str]
    progress: dict[str, Any]
    current_node: str


def create_initial_state(
    input: str = "",
    context: dict[str, Any] | None = None,
) -> BaseState:
    return BaseState(
        input=input,
        output="",
        context=context or {},
        errors=[],
        metadata={},
        node_history=[],
        progress={
            "current_node": "",
            "progress_pct": 0.0,
            "message": "Initializing",
            "started_at": None,
            "completed_nodes": [],
            "node_timings": {},
        },
        current_node="",
    )


class JobProcessingState(BaseState):
    raw_content: str
    job_title: str
    job_company: str
    job_location: str
    job_salary: str
    job_stack: str
    job_description: str
    job_requirements: str
    job_benefits: str
    job_url: str
    job_num: int
    fit_score: Optional[float]
    success_score: Optional[float]
    overall_score: Optional[float]
    score: str
    success: str
    match: str
    extraction_data: dict[str, Any]
    structured_data: dict[str, Any]
    summary_data: dict[str, Any]
    resume_text: str
    linkedin_text: str
    rules: str
    notes_text: str
    links_text: str
    session_id: str


class CompanyProcessingState(BaseState):
    raw_content: str
    company_name: str
    company_type: str
    extraction_data: dict[str, Any]
    intelligence_data: dict[str, Any]
    scores: dict[str, Any]
    company_id: Optional[int]


class InsightsState(BaseState):
    section: str
    section_data: dict[str, Any]
    all_results: dict[str, Any]
    errors_list: list[str]


class SkillRoadmapState(BaseState):
    skill_name: str
    job_type: str
    job_id: int
    items: list[dict[str, Any]]
    version: int
    session_id: str
    provider_name: str


class CheckpointConfig(TypedDict, total=False):
    enabled: bool
    db_url: str
    table_name: str
    thread_id: str


# ── Structured Output Models ────────────────────────────────────────

class JobExtractionOutput(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    salary: str = ""
    stack: str = ""
    description: str = ""
    requirements: str = ""
    benefits: str = ""
    url: str = ""

    @classmethod
    def _list_to_str(cls, v: Any) -> str:
        if isinstance(v, list):
            return "\n".join(str(item) for item in v)
        return str(v) if v is not None else ""

    @classmethod
    def _normalize(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, list):
                    data[k] = "\n".join(str(item) for item in v)
        return data

    @classmethod
    def from_llm_extraction(cls, extraction: dict, url: str = "") -> "JobExtractionOutput":
        data = cls._normalize(extraction)
        return cls(
            company=data.get("company", "Unknown"),
            title=data.get("title", "Unknown"),
            location=data.get("location", ""),
            salary=data.get("salary", ""),
            stack=data.get("stack", ""),
            description=data.get("description", ""),
            requirements=data.get("requirements", ""),
            benefits=data.get("benefits", ""),
            url=url,
        )


class JobAnalysisOutput(BaseModel):
    extraction: JobExtractionOutput = Field(default_factory=JobExtractionOutput)
    tech_stack: list[str] = Field(default_factory=list)
    requirements_analysis: dict[str, Any] = Field(default_factory=dict)
    score: str = ""
    fit_score: Optional[float] = None
    success_score: Optional[float] = None
    overall_score: Optional[float] = None
    summary: str = ""


class CompanyExtractionOutput(BaseModel):
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
    extraction: CompanyExtractionOutput = Field(default_factory=CompanyExtractionOutput)
    scores: dict[str, Any] = Field(default_factory=dict)
    intelligence: dict[str, Any] = Field(default_factory=dict)
    rules: dict[str, Any] = Field(default_factory=dict)


class ResumeOutput(BaseModel):
    resume_text: str = ""
    tailored_sections: list[dict[str, Any]] = Field(default_factory=list)
    match_score: Optional[float] = None
    suggestions: list[str] = Field(default_factory=list)


class CoverLetterOutput(BaseModel):
    cover_letter: str = ""
    paragraphs: list[str] = Field(default_factory=list)
    tone: str = "professional"
    key_highlights: list[str] = Field(default_factory=list)


class SkillExtractionOutput(BaseModel):
    skills: list[dict[str, Any]] = Field(default_factory=list)
    categories: dict[str, list[str]] = Field(default_factory=dict)
    raw_skills: list[str] = Field(default_factory=list)


class SkillRoadmapOutput(BaseModel):
    roadmap: list[dict[str, Any]] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    estimated_timelines: dict[str, str] = Field(default_factory=dict)
    learning_resources: list[dict[str, Any]] = Field(default_factory=list)


class InsightSectionOutput(BaseModel):
    section: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    recommendations: list[str] = Field(default_factory=list)


class CareerInsightsOutput(BaseModel):
    overview: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    skills: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    market: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    companies: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    networking: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    opportunities: InsightSectionOutput = Field(default_factory=InsightSectionOutput)
    health_score: Optional[float] = None
    generated_sections: list[str] = Field(default_factory=list)
