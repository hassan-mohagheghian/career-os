"""PrepareCompanyNode — gathers the inputs for the combined company analysis.

Loads the enabled scoring rules for the company scope (derived from the
company type) and stores the formatted prompt inputs on the analysis context.
"""

from __future__ import annotations

from typing import Any

from processing.application.services.company_analysis_inputs import (
    build_company_type_line,
    build_scoring_rules_text,
    scope_for_company_type,
)
from processing.application.workflows import progress_ops
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_ID = "prepare_company"


class PrepareCompanyNode:
    def __init__(
        self,
        rule_repo: Any,
        event_publisher: Any | None = None,
    ):
        self._rules = rule_repo
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        company = state.company
        company_type = (company.company_type if company else None) or "UNKNOWN"
        scope = scope_for_company_type(company_type)

        try:
            rule_rows = self._rules.get_enabled_by_scopes(["SHARED", scope])
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to load scoring rules: {e}")
            rule_rows = []

        state.analysis_context["company_text"] = (
            state.processing_context.combined_text if state.processing_context else ""
        )
        state.analysis_context["company_type"] = build_company_type_line(company_type)
        state.analysis_context["scoring_rules"] = build_scoring_rules_text(rule_rows)
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
