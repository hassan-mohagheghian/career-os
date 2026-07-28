from __future__ import annotations

import json
from typing import Any

from ..runtime.graph import GraphBuilder
from ..runtime.state import BaseState, CompanyExtractionOutput, CompanyAnalysisOutput


def build_company_processing_graph() -> GraphBuilder:

    def validate_input(state: BaseState) -> BaseState:
        content = state["context"].get("content", state["input"])

        if not content or len(content.strip()) < 10:
            state["errors"].append("No company content provided")
            return state

        state["metadata"]["validation"] = {"valid": True, "content_length": len(content)}
        return state

    def fetch_content(state: BaseState) -> BaseState:
        content = state["context"].get("content", state["input"])
        state["metadata"]["raw_content"] = content
        state["metadata"]["content_length"] = len(content)
        state["metadata"]["fetch"] = {"success": True, "length": len(content)}
        return state

    def extract_company_data(state: BaseState) -> BaseState:
        content = state["metadata"].get("raw_content", "")

        if not content:
            state["errors"].append("No content available for extraction")
            return state

        try:
            from shared.infrastructure.ai.compat import get_llm_service
            from shared.infrastructure.prompts.loader import load_prompt

            input_type = "multi_note"
            prompt = load_prompt(
                "company/company_extract",
                content=content[:8000],
                input_type=input_type,
            )

            llm = get_llm_service()
            resp = llm.generate_structured(
                prompt,
                timeout=180,
            )
            result = json.loads(resp.content)

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

    def _load_company_rules(company_type: str = "UNKNOWN") -> str:
        try:
            from dependencies import get_session_sync
            from career.infrastructure.repositories.sa_preference_repository import SQLAlchemyPreferenceRepository

            scope_map = {
                "PRODUCT_COMPANY": "COMPANY_PRODUCT",
                "RECRUITING_AGENCY": "COMPANY_RECRUITING",
                "STAFFING_COMPANY": "COMPANY_RECRUITING",
                "CONSULTING_COMPANY": "COMPANY_PRODUCT",
                "UNKNOWN": "COMPANY_PRODUCT",
            }
            entity_scope = scope_map.get(company_type, "COMPANY_PRODUCT")

            session = get_session_sync()
            try:
                pref_repo = SQLAlchemyPreferenceRepository(session)
                rows = pref_repo.get_enabled_by_scopes(["SHARED", entity_scope])
            finally:
                session.close()

            if not rows:
                return "No scoring rules set."
            lines = []
            current_cat = None
            for r in rows:
                cat = r["category"]
                if cat != current_cat:
                    current_cat = cat
                    lines.append(f"\n── {cat.upper()} {'─' * (35 - len(cat))}")
                weight = r.get("score_weight") or r["priority"]
                lines.append(f"  #{r['priority']:>3}  {r['key']} (weight:{weight}): {r['value']}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error loading rules: {e}"

    def analyze_company(state: BaseState) -> BaseState:
        extraction = state["metadata"].get("extraction", {})

        if not extraction:
            state["errors"].append("No extraction data to analyze")
            return state

        try:
            from shared.infrastructure.ai.compat import get_llm_service
            from shared.infrastructure.prompts.loader import load_prompt

            company_type = extraction.get("company_type", "UNKNOWN")
            rules = _load_company_rules(company_type)

            prompt = load_prompt(
                "company/company_analyze",
                company_data=json.dumps(extraction, ensure_ascii=False)[:4000],
                company_type=company_type,
                rules=rules,
            )

            llm = get_llm_service()
            resp = llm.generate_structured(
                prompt,
                timeout=300,
            )
            result = json.loads(resp.content)

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

    builder.set_retry("extract_company_data", max_retries=2, delay=1.0)
    builder.set_retry("analyze_company", max_retries=2, delay=1.0)

    return builder
