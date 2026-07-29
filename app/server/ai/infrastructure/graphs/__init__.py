"""AI Agent implementations — LangGraph-based workflow graphs.

Each graph is a self-contained workflow that:
- Owns its own prompts
- Returns strongly typed Pydantic models
- Supports retry, checkpointing, streaming
- Can be executed independently or composed

Graph Registry:
- job_processing: Job posting analysis pipeline
- company_processing: Company intelligence pipeline
- resume_generation: Tailored resume creation
- cover_letter_generation: Cover letter creation
- skill_extraction: Skill extraction from job postings
- skill_roadmap: Learning roadmap generation
- insights: Career intelligence (6 child graphs)
- generate_all: Parent orchestrator for all workflows
"""

from __future__ import annotations

from typing import Any

from .runtime.graph import GraphBuilder, CompiledGraph
from .runtime.state import (
    BaseState,
    create_initial_state,
    JobProcessingState,
    CompanyProcessingState,
    SkillRoadmapState,
    CheckpointConfig,
    JobExtractionOutput,
    JobAnalysisOutput,
    CompanyExtractionOutput,
    CompanyAnalysisOutput,
    ResumeOutput,
    CoverLetterOutput,
    SkillExtractionOutput,
    SkillRoadmapOutput,
)
from .runtime.executor import AgentExecutor
from .runtime.registry import AgentRegistry, AgentMetadata


def get_all_graphs() -> dict[str, GraphBuilder]:
    """Get all available workflow graphs.

    Returns:
        Dict mapping graph name to GraphBuilder instance.
    """
    from .job.graph import build_job_processing_graph
    from .company.graph import build_company_processing_graph
    from jobs.infrastructure.ai.graphs.generator import build_resume_generation_graph
    from jobs.infrastructure.ai.graphs.cover_letter import build_cover_letter_graph
    from .skills.extraction import build_skill_extraction_graph
    from .skills.roadmap import build_skill_roadmap_graph
    return {
        "job_processing": build_job_processing_graph(),
        "company_processing": build_company_processing_graph(),
        "resume_generation": build_resume_generation_graph(),
        "cover_letter_generation": build_cover_letter_graph(),
        "skill_extraction": build_skill_extraction_graph(),
        "skill_roadmap": build_skill_roadmap_graph(),
    }


def get_graph(name: str) -> GraphBuilder:
    """Get a specific workflow graph by name.

    Args:
        name: Graph name (e.g., 'job_processing', 'insights').

    Returns:
        GraphBuilder instance.

    Raises:
        ValueError: If graph name is not found.
    """
    graphs = get_all_graphs()
    if name not in graphs:
        available = ", ".join(graphs.keys())
        raise ValueError(f"Unknown graph: {name}. Available: {available}")
    return graphs[name]


__all__ = [
    "BaseState",
    "create_initial_state",
    "JobProcessingState",
    "CompanyProcessingState",
    "SkillRoadmapState",
    "CheckpointConfig",
    "JobExtractionOutput",
    "JobAnalysisOutput",
    "CompanyExtractionOutput",
    "CompanyAnalysisOutput",
    "ResumeOutput",
    "CoverLetterOutput",
    "SkillExtractionOutput",
    "SkillRoadmapOutput",

    "GraphBuilder",
    "CompiledGraph",
    "AgentExecutor",
    "AgentRegistry",
    "AgentMetadata",
    "get_all_graphs",
    "get_graph",
]
