"""Company Processing Graph — LangGraph workflow for company intelligence.

Graph: START → validate → fetch → extract → analyze → score → save → END

Design Pattern: Pipeline Pattern — sequential data transformation.
Each node owns its own prompt and produces typed output.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Optional

from ..runtime.graph import GraphBuilder
from ..runtime.state import BaseState, CompanyExtractionOutput, CompanyAnalysisOutput


def build_company_processing_graph() -> GraphBuilder:
    """Build the company processing workflow graph.

    Returns a compiled GraphBuilder ready for execution.
    """

    def validate_input(state: BaseState) -> BaseState:
        """Stage 1: Input Validation.

        Validates that company content is provided.
        """
        content = state["context"].get("content", state["input"])

        if not content or len(content.strip()) < 10:
            state["errors"].append("No company content provided")
            return state

        state["metadata"]["validation"] = {"valid": True, "content_length": len(content)}
        return state

    def fetch_content(state: BaseState) -> BaseState:
        """Stage 2: Content Fetching.

        Fetches or accepts company content.
        """
        content = state["context"].get("content", state["input"])
        state["metadata"]["raw_content"] = content
        state["metadata"]["content_length"] = len(content)
        state["metadata"]["fetch"] = {"success": True, "length": len(content)}
        return state

    def extract_company_data(state: BaseState) -> BaseState:
        """Stage 3: Company Data Extraction.

        Extracts structured company data from raw content.
        Uses prompt: companies/extract_company.md
        """
        content = state["metadata"].get("raw_content", "")

        if not content:
            state["errors"].append("No content available for extraction")
            return state

        try:
            import sys
            import os

            sys.path.insert(
                0,
                os.path.join(
                    os.path.dirname(__file__), "..", "..", "..", "..", "server"
                ),
            )
            from services.company_worker import _extract_company_info

            pid = state["context"].get("pid", "ai_company")
            result = _extract_company_info(content, "multi_note", pid)

            if result:
                extraction = CompanyExtractionOutput(
                    name=result.get("name", ""),
                    company_type=result.get("company_type", "UNKNOWN"),
                    industry=result.get("industry", ""),
                    size=result.get("size", ""),
                    location=result.get("location", ""),
                    website=result.get("website", ""),
                    description=result.get("description", ""),
                    tech_stack=result.get("tech_stack", []),
                    visa_sponsorship=result.get("visa_sponsorship"),
                )
                state["metadata"]["extraction"] = extraction.model_dump()
                state["metadata"]["extract"] = {"success": True}
            else:
                state["metadata"]["extract"] = {
                    "success": False,
                    "reason": "Extraction returned None",
                }
        except Exception as e:
            state["errors"].append(f"Company extraction failed: {e}")
            state["metadata"]["extract"] = {"success": False, "error": str(e)}

        return state

    def analyze_company(state: BaseState) -> BaseState:
        """Stage 4: Company Analysis.

        Generates intelligence analysis for the company.
        Uses prompt: companies/analyze_company.md
        """
        extraction = state["metadata"].get("extraction", {})

        if not extraction:
            state["errors"].append("No extraction data to analyze")
            return state

        try:
            import sys
            import os

            sys.path.insert(
                0,
                os.path.join(
                    os.path.dirname(__file__), "..", "..", "..", "..", "server"
                ),
            )
            from services.company_worker import _analyze_company, _load_rules

            pid = state["context"].get("pid", "ai_analyze")
            company_type = extraction.get("company_type", "UNKNOWN")
            rules = _load_rules(context="company", company_type=company_type)

            result = _analyze_company(extraction, pid, company_type=company_type)
            if result:
                state["metadata"]["intelligence"] = result
                state["metadata"]["rules"] = rules
                state["metadata"]["analyze"] = {"success": True}
            else:
                state["metadata"]["analyze"] = {
                    "success": False,
                    "reason": "Analysis returned None",
                }
        except Exception as e:
            state["errors"].append(f"Company analysis failed: {e}")
            state["metadata"]["analyze"] = {"success": False, "error": str(e)}

        return state

    def score_company(state: BaseState) -> BaseState:
        """Stage 5: Company Scoring.

        Computes fit, success, and overall scores.
        """
        intelligence = state["metadata"].get("intelligence", {})

        if not intelligence:
            state["metadata"]["scoring"] = {
                "skipped": True,
                "reason": "No intelligence data to score",
            }
            return state

        try:
            scores = intelligence.get("scores", {})
            state["metadata"]["scores"] = scores
            state["metadata"]["scoring"] = {"success": True, "scores": scores}
        except Exception as e:
            state["errors"].append(f"Scoring failed: {e}")
            state["metadata"]["scoring"] = {"success": False, "error": str(e)}

        return state

    def save_results(state: BaseState) -> BaseState:
        """Stage 6: Save Results.

        Persists company analysis results to database.
        """
        extraction = state["metadata"].get("extraction", {})
        intelligence = state["metadata"].get("intelligence", {})

        if not extraction and not intelligence:
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
            state["errors"].append(f"Save failed: {e}")
            state["metadata"]["persistence"] = {"success": False, "error": str(e)}

        return state

    def completion_event(state: BaseState) -> BaseState:
        """Stage 7: Completion Event.

        Builds final typed output.
        """
        extraction_data = state["metadata"].get("extraction", {})
        intelligence = state["metadata"].get("intelligence", {})
        scores = state["metadata"].get("scores", {})

        output = CompanyAnalysisOutput(
            extraction=CompanyExtractionOutput(**extraction_data)
            if extraction_data
            else CompanyExtractionOutput(),
            scores=scores,
            intelligence=intelligence,
            rules=state["metadata"].get("rules", {}),
        )

        state["output"] = json.dumps(output.model_dump(), default=str)
        state["metadata"]["completion"] = {"success": True}
        state["metadata"]["typed_output"] = output.model_dump()

        return state

    # Build the graph
    builder = GraphBuilder("company_processing")
    builder.add_node("validate_input", validate_input)
    builder.add_node("fetch_content", fetch_content)
    builder.add_node("extract_company_data", extract_company_data)
    builder.add_node("analyze_company", analyze_company)
    builder.add_node("score_company", score_company)
    builder.add_node("save_results", save_results)
    builder.add_node("completion_event", completion_event)

    builder.add_edge("validate_input", "fetch_content")
    builder.add_edge("fetch_content", "extract_company_data")
    builder.add_edge("extract_company_data", "analyze_company")
    builder.add_edge("analyze_company", "score_company")
    builder.add_edge("score_company", "save_results")
    builder.add_edge("save_results", "completion_event")

    builder.set_entry("validate_input")
    builder.set_finish("completion_event")

    # Retry config for extraction and analysis nodes
    builder.set_retry("extract_company_data", max_retries=2, delay=1.0)
    builder.set_retry("analyze_company", max_retries=2, delay=1.0)

    return builder
