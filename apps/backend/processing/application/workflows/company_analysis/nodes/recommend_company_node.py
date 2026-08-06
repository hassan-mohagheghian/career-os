"""RecommendCompanyNode — finalizes the company recommendation.

The recommendation priority is derived deterministically from the overall
score; the strategic text comes from the LLM (with a sensible fallback).
"""

from __future__ import annotations

from typing import Any

from processing.application.services.company_analysis_scoring import grade_for_overall
from processing.application.workflows import progress_ops
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_ID = "recommend_company"


class RecommendCompanyNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        result = state.analysis_result
        if result is not None:
            overall = (result.get("scores") or {}).get("overall")
            recommendation = result.get("recommendation") or {}
            if not recommendation.get("priority"):
                recommendation["priority"] = grade_for_overall(overall)
            if not recommendation.get("action"):
                recommendation["action"] = (
                    f"Apply when a fitting role opens; overall company score is {overall}."
                )
            result["recommendation"] = recommendation
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
