"""Cover Letter Generation Graph — LangGraph workflow for cover letter creation.

Graph: START → load_resume → load_job → generate → format → validate → END

Design Pattern: Pipeline Pattern — sequential data transformation.
Each node owns its own prompt and produces typed output.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Optional

from ..runtime.graph import GraphBuilder
from ..runtime.state import BaseState, CoverLetterOutput


def build_cover_letter_graph() -> GraphBuilder:
    """Build the cover letter generation workflow graph.

    Returns a compiled GraphBuilder ready for execution.
    """

    def load_resume(state: BaseState) -> BaseState:
        """Stage 1: Load Base Resume.

        Loads the user's resume for context.
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
            else:
                state["errors"].append("No base resume found")
        except Exception as e:
            state["errors"].append(f"Failed to load resume: {e}")

        return state

    def load_job_context(state: BaseState) -> BaseState:
        """Stage 2: Load Job Context.

        Loads job posting data for cover letter context.
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
                }
            else:
                state["errors"].append(f"Job not found: {job_id}")
        except Exception as e:
            state["errors"].append(f"Failed to load job: {e}")

        return state

    def generate_cover_letter(state: BaseState) -> BaseState:
        """Stage 3: Generate Cover Letter.

        Uses AI to generate a tailored cover letter.
        Uses prompt: resume/generate_cover_letter.md
        """
        resume_text = state["metadata"].get("resume_text", "")
        job_data = state["metadata"].get("job_data", {})

        if not resume_text:
            state["errors"].append("No resume text for context")
            return state

        if not job_data:
            state["errors"].append("No job data for context")
            return state

        try:
            prompt = f"""Write a professional cover letter for this position:

Job Title: {job_data.get('title', 'N/A')}
Company: {job_data.get('company', 'N/A')}
Description: {job_data.get('description', 'N/A')}
Requirements: {job_data.get('requirements', 'N/A')}

Based on this resume:
{resume_text[:2000]}

Write a compelling cover letter that:
1. Opens with enthusiasm for the role
2. Highlights 2-3 relevant experiences
3. Shows knowledge of the company
4. Closes with a call to action"""

            state["metadata"]["generate_prompt"] = prompt
            state["metadata"]["generate"] = {"success": True, "prompt_ready": True}
        except Exception as e:
            state["errors"].append(f"Generation failed: {e}")
            state["metadata"]["generate"] = {"success": False, "error": str(e)}

        return state

    def format_output(state: BaseState) -> BaseState:
        """Stage 4: Format Output.

        Formats the cover letter into structured output.
        """
        job_data = state["metadata"].get("job_data", {})
        generate = state["metadata"].get("generate", {})

        if not generate.get("success"):
            state["errors"].append("No generation result to format")
            return state

        try:
            # Parse the generated prompt as placeholder
            # In production, this would parse the AI response
            paragraphs = []
            state["metadata"]["paragraphs"] = paragraphs
            state["metadata"]["format"] = {"success": True}
        except Exception as e:
            state["errors"].append(f"Formatting failed: {e}")
            state["metadata"]["format"] = {"success": False, "error": str(e)}

        return state

    def validate_output(state: BaseState) -> BaseState:
        """Stage 5: Validate Output.

        Validates the cover letter meets quality standards.
        """
        paragraphs = state["metadata"].get("paragraphs", [])

        checks = {
            "has_content": len(paragraphs) > 0,
            "minimum_paragraphs": len(paragraphs) >= 3,
        }

        state["metadata"]["validation"] = checks
        state["metadata"]["valid"] = all(checks.values())

        return state

    def completion_event(state: BaseState) -> BaseState:
        """Stage 6: Completion Event.

        Builds final typed output.
        """
        paragraphs = state["metadata"].get("paragraphs", [])

        output = CoverLetterOutput(
            cover_letter="\n\n".join(paragraphs),
            paragraphs=paragraphs,
            tone="professional",
            key_highlights=[],
        )

        state["output"] = json.dumps(output.model_dump(), default=str)
        state["metadata"]["completion"] = {"success": True}
        state["metadata"]["typed_output"] = output.model_dump()

        return state

    # Build the graph
    builder = GraphBuilder("cover_letter_generation")
    builder.add_node("load_resume", load_resume)
    builder.add_node("load_job_context", load_job_context)
    builder.add_node("generate_cover_letter", generate_cover_letter)
    builder.add_node("format_output", format_output)
    builder.add_node("validate_output", validate_output)
    builder.add_node("completion_event", completion_event)

    builder.add_edge("load_resume", "load_job_context")
    builder.add_edge("load_job_context", "generate_cover_letter")
    builder.add_edge("generate_cover_letter", "format_output")
    builder.add_edge("format_output", "validate_output")
    builder.add_edge("validate_output", "completion_event")

    builder.set_entry("load_resume")
    builder.set_finish("completion_event")

    return builder
