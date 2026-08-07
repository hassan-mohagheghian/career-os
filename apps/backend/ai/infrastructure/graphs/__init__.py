"""AI Agent implementations — LangGraph-based workflow graphs.

Each graph is a self-contained workflow that:
- Owns its own prompts
- Returns strongly typed Pydantic models
- Supports retry, checkpointing, streaming
- Can be executed independently or composed

Graph Registry:
- job_processing: Job posting analysis pipeline
- skill_extraction: Skill extraction from job postings
- insights: Career intelligence (6 child graphs)
"""

from __future__ import annotations

from typing import Any

from .runtime.graph import GraphBuilder, CompiledGraph
from .runtime.state import (
    BaseState,
    create_initial_state,
    JobProcessingState,
    CheckpointConfig,
    JobExtractionOutput,
    JobAnalysisOutput,
    SkillExtractionOutput,
)
from .runtime.executor import AgentExecutor
from .runtime.registry import AgentRegistry, AgentMetadata


def get_all_graphs() -> dict[str, GraphBuilder]:
    """Get all available workflow graphs.

    Returns:
        Dict mapping graph name to GraphBuilder instance.
    """
    from .job.graph import build_job_processing_graph
    from .skills.extraction import build_skill_extraction_graph
    return {
        "job_processing": build_job_processing_graph(),
        "skill_extraction": build_skill_extraction_graph(),
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
    "CheckpointConfig",
    "JobExtractionOutput",
    "JobAnalysisOutput",
    "SkillExtractionOutput",

    "GraphBuilder",
    "CompiledGraph",
    "AgentExecutor",
    "AgentRegistry",
    "AgentMetadata",
    "get_all_graphs",
    "get_graph",
]
