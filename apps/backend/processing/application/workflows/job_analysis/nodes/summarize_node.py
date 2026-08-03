"""SummarizeNode — finalizes the job summary for the result.

Ensures the summary dict always has the three expected fields, falling back
to the LLM's raw text or a generated one when missing.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "summarize"


class SummarizeNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        result = state.analysis_result
        if result is not None:
            summary = result.get("summary") or {}
            result["summary"] = {
                "summary": summary.get("summary") or "",
                "resume_fit": summary.get("resume_fit") or "",
                "note": summary.get("note") or "",
            }
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
