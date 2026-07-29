"""Generate All Graph — parent LangGraph orchestrator.

Orchestrates all child workflow graphs in sequence.
Each child graph remains independently executable.

Graph: START → job_processing → company_processing → resume →
       cover_letter → skill_extraction → skill_roadmap → END
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Optional

from .runtime.graph import GraphBuilder
from .runtime.state import BaseState

# Import child graph builders
from .job.graph import build_job_processing_graph
from .company.graph import build_company_processing_graph
from jobs.infrastructure.ai.graphs.generator import build_resume_generation_graph
from jobs.infrastructure.ai.graphs.cover_letter import build_cover_letter_graph
from .skills.extraction import build_skill_extraction_graph
from .skills.roadmap import build_skill_roadmap_graph


def build_generate_all_graph() -> GraphBuilder:
    """Build the Generate All parent orchestrator graph.

    This graph coordinates all child workflow graphs. Each child
    graph is compiled and executed as a sub-graph within the pipeline.

    If a child graph fails, the error is recorded but the pipeline
    continues to the next child graph.

    Returns a compiled GraphBuilder ready for execution.
    """
    # Build and compile child graphs
    job_graph = build_job_processing_graph().compile()
    company_graph = build_company_processing_graph().compile()
    resume_graph = build_resume_generation_graph().compile()
    cover_letter_graph = build_cover_letter_graph().compile()
    skill_extraction_graph = build_skill_extraction_graph().compile()
    skill_roadmap_graph = build_skill_roadmap_graph().compile()

    def run_job_processing(state: BaseState) -> BaseState:
        """Execute job processing child graph."""
        state["metadata"]["current_stage"] = "job_processing"
        try:
            result = job_graph.invoke(state)
            state["metadata"]["job_processing"] = {
                "success": True,
                "output": result.get("output", ""),
                "errors": result.get("errors", []),
            }
        except Exception as e:
            state["errors"].append(f"Job processing failed: {e}")
            state["metadata"]["job_processing"] = {"success": False, "error": str(e)}
        return state

    def run_company_processing(state: BaseState) -> BaseState:
        """Execute company processing child graph."""
        state["metadata"]["current_stage"] = "company_processing"
        try:
            result = company_graph.invoke(state)
            state["metadata"]["company_processing"] = {
                "success": True,
                "output": result.get("output", ""),
                "errors": result.get("errors", []),
            }
        except Exception as e:
            state["errors"].append(f"Company processing failed: {e}")
            state["metadata"]["company_processing"] = {"success": False, "error": str(e)}
        return state

    def run_resume_generation(state: BaseState) -> BaseState:
        """Execute resume generation child graph."""
        state["metadata"]["current_stage"] = "resume_generation"
        try:
            result = resume_graph.invoke(state)
            state["metadata"]["resume_generation"] = {
                "success": True,
                "output": result.get("output", ""),
                "errors": result.get("errors", []),
            }
        except Exception as e:
            state["errors"].append(f"Resume generation failed: {e}")
            state["metadata"]["resume_generation"] = {"success": False, "error": str(e)}
        return state

    def run_cover_letter(state: BaseState) -> BaseState:
        """Execute cover letter generation child graph."""
        state["metadata"]["current_stage"] = "cover_letter_generation"
        try:
            result = cover_letter_graph.invoke(state)
            state["metadata"]["cover_letter_generation"] = {
                "success": True,
                "output": result.get("output", ""),
                "errors": result.get("errors", []),
            }
        except Exception as e:
            state["errors"].append(f"Cover letter generation failed: {e}")
            state["metadata"]["cover_letter_generation"] = {"success": False, "error": str(e)}
        return state

    def run_skill_extraction(state: BaseState) -> BaseState:
        """Execute skill extraction child graph."""
        state["metadata"]["current_stage"] = "skill_extraction"
        try:
            result = skill_extraction_graph.invoke(state)
            state["metadata"]["skill_extraction"] = {
                "success": True,
                "output": result.get("output", ""),
                "errors": result.get("errors", []),
            }
        except Exception as e:
            state["errors"].append(f"Skill extraction failed: {e}")
            state["metadata"]["skill_extraction"] = {"success": False, "error": str(e)}
        return state

    def run_skill_roadmap(state: BaseState) -> BaseState:
        """Execute skill roadmap child graph."""
        state["metadata"]["current_stage"] = "skill_roadmap"
        try:
            result = skill_roadmap_graph.invoke(state)
            state["metadata"]["skill_roadmap"] = {
                "success": True,
                "output": result.get("output", ""),
                "errors": result.get("errors", []),
            }
        except Exception as e:
            state["errors"].append(f"Skill roadmap failed: {e}")
            state["metadata"]["skill_roadmap"] = {"success": False, "error": str(e)}
        return state

    def completion_event(state: BaseState) -> BaseState:
        """Build final aggregated output."""
        stages = [
            "job_processing", "company_processing", "resume_generation",
            "cover_letter_generation", "skill_extraction", "skill_roadmap",
        ]

        results = {}
        successful = []
        failed = []

        for stage in stages:
            stage_data = state["metadata"].get(stage, {})
            results[stage] = stage_data
            if stage_data.get("success"):
                successful.append(stage)
            else:
                failed.append(stage)

        output = {
            "stages": results,
            "successful_stages": successful,
            "failed_stages": failed,
            "total_stages": len(stages),
            "completed_count": len(successful),
            "completion_rate": round(len(successful) / len(stages) * 100, 1),
        }

        state["output"] = json.dumps(output, default=str)
        state["metadata"]["completion"] = {
            "success": len(failed) == 0,
            "results": results,
        }
        state["metadata"]["current_stage"] = "completed"

        return state

    # Build the parent graph
    builder = GraphBuilder("generate_all")
    builder.add_node("job_processing", run_job_processing)
    builder.add_node("company_processing", run_company_processing)
    builder.add_node("resume_generation", run_resume_generation)
    builder.add_node("cover_letter_generation", run_cover_letter)
    builder.add_node("skill_extraction", run_skill_extraction)
    builder.add_node("skill_roadmap", run_skill_roadmap)
    builder.add_node("completion_event", completion_event)

    builder.add_edge("job_processing", "company_processing")
    builder.add_edge("company_processing", "resume_generation")
    builder.add_edge("resume_generation", "cover_letter_generation")
    builder.add_edge("cover_letter_generation", "skill_extraction")
    builder.add_edge("skill_extraction", "skill_roadmap")
    builder.add_edge("skill_roadmap", "completion_event")

    builder.set_entry("job_processing")
    builder.set_finish("completion_event")

    # Each stage can fail independently
    builder.set_retry("job_processing", max_retries=1, delay=0.5)
    builder.set_retry("company_processing", max_retries=1, delay=0.5)
    builder.set_retry("resume_generation", max_retries=1, delay=0.5)
    builder.set_retry("cover_letter_generation", max_retries=1, delay=0.5)
    builder.set_retry("skill_extraction", max_retries=1, delay=0.5)
    builder.set_retry("skill_roadmap", max_retries=1, delay=0.5)

    return builder
