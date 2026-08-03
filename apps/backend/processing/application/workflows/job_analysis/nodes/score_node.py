"""ScoreNode — deterministic scoring of the analyzed job.

Computes fit/success/overall scores and the recommendation from the raw LLM
payload using pure helpers, so the UI always shows consistent values.
"""

from __future__ import annotations

from typing import Any

from processing.application.services.job_analysis_scoring import (
    build_analysis_result,
    normalize_payload,
)
from processing.application.workflows import progress_ops
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "score"


class ScoreNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        payload = normalize_payload(state.analysis_context.get("raw_payload"))
        result = build_analysis_result(payload)
        result["skills"] = state.analysis_context.get("normalized_skills") or []
        state.analysis_result = result
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
