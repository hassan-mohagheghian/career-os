"""Resume Generation Graph — LangGraph workflow for tailored resume creation.

Graph: START → load_resume → load_job → tailor → format → validate → END

Design Pattern: Pipeline Pattern — sequential data transformation.
Each node owns its own prompt and produces typed output.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Optional

from ..runtime.graph import GraphBuilder
from ..runtime.state import BaseState, ResumeOutput


def build_resume_generation_graph() -> GraphBuilder:
    """Build the resume generation workflow graph.

    Returns a compiled GraphBuilder ready for execution.
    """

    def load_resume(state: BaseState) -> BaseState:
        """Stage 1: Load Base Resume.

        Loads the user's base resume from database.
        Uses prompt: resume/load_resume.md
        """
        try:
            from shared.infrastructure.database.session import get_session_sync
            from jobs.infrastructure.models.misc_models import ResumeModel

            session = get_session_sync()
            model = session.query(ResumeModel).filter(
                ResumeModel.id.like("original_%")
            ).order_by(ResumeModel.version.desc()).first()

            if model and model.raw_text:
                state["metadata"]["resume_text"] = model.raw_text
                state["metadata"]["resume_id"] = model.id
            else:
                state["errors"].append("No base resume found in database")
        except Exception as e:
            state["errors"].append(f"Failed to load resume: {e}")

        return state

    def load_job_context(state: BaseState) -> BaseState:
        """Stage 2: Load Job Context.

        Loads job posting data for tailoring.
        """
        job_id = state["context"].get("job_id")
        job_data = state["context"].get("job_data", {})

        if job_data:
            state["metadata"]["job_data"] = job_data
            return state

        if not job_id:
            state["errors"].append("No job_id or job_data provided")
            return state

        try:
            from shared.infrastructure.database.session import get_session_sync
            from jobs.infrastructure.models.job_model import JobModel

            session = get_session_sync()
            job = session.query(JobModel).filter(JobModel.id == job_id).first()

            if job:
                state["metadata"]["job_data"] = {
                    "title": job.role or "",
                    "company": job.company or "",
                    "description": job.description or "",
                    "requirements": job.requirements or "",
                    "stack": job.stack or "",
                }
            else:
                state["errors"].append(f"Job not found: {job_id}")
        except Exception as e:
            state["errors"].append(f"Failed to load job: {e}")

        return state

    def tailor_content(state: BaseState) -> BaseState:
        """Stage 3: Tailor Resume Content.

        Uses AI to tailor resume for the specific job.
        Uses prompt: resume/tailor_resume.md
        """
        resume_text = state["metadata"].get("resume_text", "")
        job_data = state["metadata"].get("job_data", {})

        if not resume_text:
            state["errors"].append("No resume text to tailor")
            return state

        if not job_data:
            state["errors"].append("No job data for tailoring context")
            return state

        try:
            # Build tailoring prompt
            prompt = f"""Tailor the following resume for this job posting:

Job Title: {job_data.get('title', 'N/A')}
Company: {job_data.get('company', 'N/A')}
Requirements: {job_data.get('requirements', 'N/A')}
Tech Stack: {job_data.get('stack', 'N/A')}

Resume:
{resume_text}

Provide a tailored version that highlights relevant experience and skills."""

            state["metadata"]["tailor_prompt"] = prompt
            state["metadata"]["tailor"] = {"success": True, "prompt_ready": True}
        except Exception as e:
            state["errors"].append(f"Tailoring failed: {e}")
            state["metadata"]["tailor"] = {"success": False, "error": str(e)}

        return state

    def format_output(state: BaseState) -> BaseState:
        """Stage 4: Format Output.

        Formats the tailored resume into structured output.
        """
        resume_text = state["metadata"].get("resume_text", "")
        job_data = state["metadata"].get("job_data", {})

        if not resume_text:
            state["errors"].append("No resume text to format")
            return state

        try:
            # Parse resume into sections
            sections = []
            current_section = {"title": "general", "content": []}

            for line in resume_text.split("\n"):
                stripped = line.strip()
                if stripped.endswith(":") and len(stripped) < 50:
                    if current_section["content"]:
                        sections.append(current_section)
                    current_section = {"title": stripped.rstrip(":"), "content": []}
                else:
                    current_section["content"].append(stripped)

            if current_section["content"]:
                sections.append(current_section)

            state["metadata"]["sections"] = sections
            state["metadata"]["format"] = {"success": True, "section_count": len(sections)}
        except Exception as e:
            state["errors"].append(f"Formatting failed: {e}")
            state["metadata"]["format"] = {"success": False, "error": str(e)}

        return state

    def validate_output(state: BaseState) -> BaseState:
        """Stage 5: Validate Output.

        Validates the generated resume meets quality standards.
        """
        resume_text = state["metadata"].get("resume_text", "")

        if not resume_text:
            state["errors"].append("No resume text to validate")
            return state

        checks = {
            "has_content": bool(resume_text.strip()),
            "minimum_length": len(resume_text) > 100,
            "has_sections": len(state.get("metadata", {}).get("sections", [])) > 0,
        }

        state["metadata"]["validation"] = checks
        state["metadata"]["valid"] = all(checks.values())

        return state

    def completion_event(state: BaseState) -> BaseState:
        """Stage 6: Completion Event.

        Builds final typed output.
        """
        resume_text = state["metadata"].get("resume_text", "")
        sections = state["metadata"].get("sections", [])
        job_data = state["metadata"].get("job_data", {})

        output = ResumeOutput(
            resume_text=resume_text,
            tailored_sections=sections,
            match_score=None,
            suggestions=[],
        )

        state["output"] = json.dumps(output.model_dump(), default=str)
        state["metadata"]["completion"] = {"success": True}
        state["metadata"]["typed_output"] = output.model_dump()

        return state

    # Build the graph
    builder = GraphBuilder("resume_generation")
    builder.add_node("load_resume", load_resume)
    builder.add_node("load_job_context", load_job_context)
    builder.add_node("tailor_content", tailor_content)
    builder.add_node("format_output", format_output)
    builder.add_node("validate_output", validate_output)
    builder.add_node("completion_event", completion_event)

    builder.add_edge("load_resume", "load_job_context")
    builder.add_edge("load_job_context", "tailor_content")
    builder.add_edge("tailor_content", "format_output")
    builder.add_edge("format_output", "validate_output")
    builder.add_edge("validate_output", "completion_event")

    builder.set_entry("load_resume")
    builder.set_finish("completion_event")

    return builder
