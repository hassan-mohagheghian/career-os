"""ScoreCompanyNode — deterministic scoring of the analyzed company.

Computes fit/success/overall scores and grades from the raw LLM payload using
pure helpers, so the UI always shows consistent values.
"""

from __future__ import annotations

from typing import Any

from processing.application.services.company_analysis_scoring import (
    build_company_analysis_result,
    normalize_payload,
)
from processing.application.workflows import progress_ops
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_ID = "score_company"


class ScoreCompanyNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        payload = normalize_payload(state.analysis_context.get("raw_payload"))
        state.analysis_result = build_company_analysis_result(payload)
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
