"""RecommendNode — finalizes the recommendation and apply reason.

The recommendation is derived deterministically from the overall score; the
apply_reason text comes from the LLM (with a sensible fallback).
"""

from __future__ import annotations

from typing import Any

from processing.application.services.job_analysis_scoring import (
    coerce_recommendation,
    recommendation_for_overall,
)
from processing.application.workflows import progress_ops
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "recommend"


class RecommendNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        result = state.analysis_result
        if result is not None:
            overall = result["scores"]["overall"]
            result["recommendation"] = recommendation_for_overall(overall)
            if not result["apply_reason"]:
                raw = (state.analysis_context.get("raw_payload") or {})
                llm_rec = coerce_recommendation(raw.get("recommendation"))
                result["apply_reason"] = (
                    f"Overall score {overall}. "
                    f"Suggested action: {llm_rec}."
                )
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
