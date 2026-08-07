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
    job_id: str
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


class SkillExtractionOutput(BaseModel):
    skills: list[dict[str, Any]] = Field(default_factory=list)
    categories: dict[str, list[str]] = Field(default_factory=dict)
    raw_skills: list[str] = Field(default_factory=list)



