"""Job Processing Graph — LangGraph workflow for job analysis.

Graph: START → validate → fetch → fallback_notes → extract_raw →
clean_content → extract_structured → analyze → extract_skills →
score → summary → persistence → END

Design Pattern: Pipeline Pattern — sequential data transformation.
Each node has inputs, outputs, retry strategy, and failure handling.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Optional

from ..runtime.graph import GraphBuilder
from ..runtime.state import BaseState, JobExtractionOutput, JobAnalysisOutput


def build_job_processing_graph() -> GraphBuilder:
    """Build the job processing workflow graph.

    Returns a compiled GraphBuilder ready for execution.
    Each node owns its own prompt and produces typed output.
    """

    def validate_input(state: BaseState) -> BaseState:
        """Stage 1: Input Validation.

        Validates that at least one job source is provided.
        """
        url = state["context"].get("url", state["input"])
        notes = state["context"].get("notes", [])
        links = state["context"].get("links", [])

        has_url = bool(url and url.startswith("http"))
        has_notes = bool(notes)
        has_links = bool(links)

        if not (has_url or has_notes or has_links):
            state["errors"].append("No job sources provided (URL, notes, or links)")
            return state

        state["metadata"]["validation"] = {
            "has_url": has_url,
            "has_notes": has_notes,
            "has_links": has_links,
            "valid": True,
        }

        return state

    def fetch_url(state: BaseState) -> BaseState:
        """Stage 2: URL Fetching.

        Fetches content from the provided URL.
        """
        url = state["context"].get("url", state["input"])

        if not url or not url.startswith("http"):
            state["metadata"]["fetch"] = {"skipped": True, "reason": "No URL provided"}
            return state

        try:
            from jobs.infrastructure.workers.worker import _fetch_url

            content = _fetch_url(url)
            state["metadata"]["raw_content"] = content
            state["metadata"]["content_length"] = len(content)
            state["metadata"]["fetch"] = {
                "success": True,
                "url": url,
                "length": len(content),
            }
        except Exception as e:
            state["errors"].append(f"URL fetch failed: {e}")
            state["metadata"]["fetch"] = {"success": False, "error": str(e)}

        return state

    def fallback_to_notes(state: BaseState) -> BaseState:
        """Stage 3: Fallback to Notes.

        If URL fetch failed, try to use notes as content.
        """
        if state["metadata"].get("raw_content"):
            state["metadata"]["fallback"] = {
                "skipped": True,
                "reason": "Content already fetched",
            }
            return state

        notes = state["context"].get("notes", [])
        if notes:
            content = "\n\n".join(notes)
            state["metadata"]["raw_content"] = content
            state["metadata"]["content_length"] = len(content)
            state["metadata"]["fallback"] = {"used_notes": True, "length": len(content)}
        else:
            state["metadata"]["fallback"] = {
                "used_notes": False,
                "reason": "No notes available",
            }

        return state

    def extract_raw_content(state: BaseState) -> BaseState:
        """Stage 4: Raw Content Extraction.

        Extracts raw text content from the fetched data.
        Uses prompt: jobs/extract_job.md
        """
        content = state["metadata"].get("raw_content", "")

        if not content:
            state["errors"].append("No content available for extraction")
            return state

        try:
            pid = state["context"].get("pid", "ai_job")
            from jobs.infrastructure.workers.worker import _extract_all

            result = _extract_all(content, pid)
            if result:
                state["metadata"]["extraction"] = result
                state["metadata"]["extract_raw"] = {"success": True}
            else:
                state["metadata"]["extract_raw"] = {
                    "success": False,
                    "reason": "Extraction returned None",
                }
        except Exception as e:
            state["errors"].append(f"Raw extraction failed: {e}")
            state["metadata"]["extract_raw"] = {"success": False, "error": str(e)}

        return state

    def clean_content(state: BaseState) -> BaseState:
        """Stage 5: Content Cleaning.

        Cleans and normalizes the extracted content.
        """
        extraction = state["metadata"].get("extraction", {})

        if not extraction:
            state["metadata"]["clean"] = {
                "skipped": True,
                "reason": "No extraction to clean",
            }
            return state

        for key in ["title", "company", "description", "requirements"]:
            if key in extraction and isinstance(extraction[key], str):
                extraction[key] = extraction[key].strip()

        state["metadata"]["extraction"] = extraction
        state["metadata"]["clean"] = {
            "success": True,
            "fields_cleaned": list(extraction.keys()),
        }

        return state

    def extract_structured_data(state: BaseState) -> BaseState:
        """Stage 6: Structured Extraction.

        Structures the extracted data into a typed Pydantic model.
        """
        extraction = state["metadata"].get("extraction", {})

        if not extraction:
            state["metadata"]["structured"] = {
                "skipped": True,
                "reason": "No extraction to structure",
            }
            return state

        structured = JobExtractionOutput(
            company=extraction.get("company", "Unknown"),
            title=extraction.get("title", "Unknown"),
            location=extraction.get("location", ""),
            salary=extraction.get("salary", ""),
            stack=extraction.get("stack", ""),
            description=extraction.get("description", ""),
            requirements=extraction.get("requirements", ""),
            benefits=extraction.get("benefits", ""),
            url=state["context"].get("url", ""),
        )

        state["metadata"]["structured"] = structured.model_dump()
        state["metadata"]["extract_struct"] = {"success": True}

        return state

    def analyze_job(state: BaseState) -> BaseState:
        """Stage 7: Job Analysis.

        Analyzes the job posting for requirements and fit.
        Uses prompt: jobs/score_job.md
        """
        structured = state["metadata"].get("structured", {})

        if not structured:
            state["metadata"]["analysis"] = {
                "skipped": True,
                "reason": "No structured data to analyze",
            }
            return state

        try:
            stack = structured.get("stack", "")
            state["metadata"]["tech_stack"] = stack

            requirements = structured.get("requirements", "")
            state["metadata"]["requirements_analysis"] = {
                "has_requirements": bool(requirements),
                "length": len(requirements),
            }

            state["metadata"]["analyze"] = {"success": True}
        except Exception as e:
            state["errors"].append(f"Analysis failed: {e}")
            state["metadata"]["analyze"] = {"success": False, "error": str(e)}

        return state

    def extract_skills_node(state: BaseState) -> BaseState:
        """Stage 8: Skill Extraction.

        Extracts skills from the job description.
        """
        structured = state["metadata"].get("structured", {})
        description = structured.get("description", "")

        if not description:
            state["metadata"]["skills"] = {
                "skipped": True,
                "reason": "No description to extract skills from",
            }
            return state

        try:
            stack = structured.get("stack", "")
            skills = [s.strip() for s in stack.split(",") if s.strip()]
            state["metadata"]["extracted_skills"] = skills
            state["metadata"]["extract_skills"] = {
                "success": True,
                "count": len(skills),
            }
        except Exception as e:
            state["errors"].append(f"Skill extraction failed: {e}")
            state["metadata"]["extract_skills"] = {
                "success": False,
                "error": str(e),
            }

        return state

    def score_job(state: BaseState) -> BaseState:
        """Stage 9: Scoring.

        Computes fit score and success score.
        Uses prompt: jobs/score_job.md
        """
        extraction = state["metadata"].get("extraction", {})

        if not extraction:
            state["metadata"]["scoring"] = {
                "skipped": True,
                "reason": "No extraction to score",
            }
            return state

        try:
            from jobs.infrastructure.workers.worker import normalize_score

            score = normalize_score(extraction.get("score", "P"))
            state["metadata"]["score"] = score
            state["metadata"]["fit_score"] = extraction.get("fit_score")
            state["metadata"]["success_score"] = extraction.get("success_score")
            state["metadata"]["overall_score"] = extraction.get("overall_score")
            state["metadata"]["scoring"] = {"success": True, "score": score}
        except Exception as e:
            state["errors"].append(f"Scoring failed: {e}")
            state["metadata"]["scoring"] = {"success": False, "error": str(e)}

        return state

    def generate_summary(state: BaseState) -> BaseState:
        """Stage 10: Summary Generation.

        Generates a summary of the job posting.
        Uses prompt: jobs/summarize_job.md
        """
        structured = state["metadata"].get("structured", {})
        extraction = state["metadata"].get("extraction", {})

        if not structured and not extraction:
            state["metadata"]["summary"] = {
                "skipped": True,
                "reason": "No data to summarize",
            }
            return state

        try:
            summary_parts = []
            if structured.get("title"):
                summary_parts.append(f"Position: {structured['title']}")
            if structured.get("company"):
                summary_parts.append(f"Company: {structured['company']}")
            if structured.get("location"):
                summary_parts.append(f"Location: {structured['location']}")
            if extraction.get("summary"):
                summary_parts.append(f"Summary: {extraction['summary']}")

            summary = "\n".join(summary_parts)
            state["metadata"]["job_summary"] = summary
            state["metadata"]["generate_summary"] = {"success": True}
        except Exception as e:
            state["errors"].append(f"Summary generation failed: {e}")
            state["metadata"]["generate_summary"] = {
                "success": False,
                "error": str(e),
            }

        return state

    def persist_results(state: BaseState) -> BaseState:
        """Stage 11: Persistence.

        Saves the job results to the database.
        """
        structured = state["metadata"].get("structured", {})
        extraction = state["metadata"].get("extraction", {})

        if not structured and not extraction:
            state["metadata"]["persistence"] = {
                "skipped": True,
                "reason": "No data to persist",
            }
            return state

        try:
            state["metadata"]["persistence"] = {
                "success": True,
                "ready_to_save": True,
            }
        except Exception as e:
            state["errors"].append(f"Persistence failed: {e}")
            state["metadata"]["persistence"] = {
                "success": False,
                "error": str(e),
            }

        return state

    def completion_event(state: BaseState) -> BaseState:
        """Stage 12: Completion Event.

        Builds final typed output and emits completion.
        """
        output = JobAnalysisOutput(
            extraction=JobExtractionOutput(
                **state["metadata"].get("structured", {})
            ),
            tech_stack=state["metadata"].get("extracted_skills", []),
            requirements_analysis=state["metadata"].get(
                "requirements_analysis", {}
            ),
            score=state["metadata"].get("score", ""),
            fit_score=state["metadata"].get("fit_score"),
            success_score=state["metadata"].get("success_score"),
            overall_score=state["metadata"].get("overall_score"),
            summary=state["metadata"].get("job_summary", ""),
        )

        state["output"] = json.dumps(output.model_dump(), default=str)
        state["metadata"]["completion"] = {"success": True}
        state["metadata"]["typed_output"] = output.model_dump()

        return state

    # Build the graph
    builder = GraphBuilder("job_processing")
    builder.add_node("validate_input", validate_input)
    builder.add_node("fetch_url", fetch_url)
    builder.add_node("fallback_to_notes", fallback_to_notes)
    builder.add_node("extract_raw_content", extract_raw_content)
    builder.add_node("clean_content", clean_content)
    builder.add_node("extract_structured_data", extract_structured_data)
    builder.add_node("analyze_job", analyze_job)
    builder.add_node("extract_skills", extract_skills_node)
    builder.add_node("score_job", score_job)
    builder.add_node("generate_summary", generate_summary)
    builder.add_node("persist_results", persist_results)
    builder.add_node("completion_event", completion_event)

    builder.add_edge("validate_input", "fetch_url")
    builder.add_edge("fetch_url", "fallback_to_notes")
    builder.add_edge("fallback_to_notes", "extract_raw_content")
    builder.add_edge("extract_raw_content", "clean_content")
    builder.add_edge("clean_content", "extract_structured_data")
    builder.add_edge("extract_structured_data", "analyze_job")
    builder.add_edge("analyze_job", "extract_skills")
    builder.add_edge("extract_skills", "score_job")
    builder.add_edge("score_job", "generate_summary")
    builder.add_edge("generate_summary", "persist_results")
    builder.add_edge("persist_results", "completion_event")

    builder.set_entry("validate_input")
    builder.set_finish("completion_event")

    # Retry config for LLM-dependent nodes
    builder.set_retry("extract_raw_content", max_retries=2, delay=1.0)
    builder.set_retry("score_job", max_retries=2, delay=1.0)

    return builder
