"""BuildContextNode — creates the final JobProcessingContext.

Delegates to JobContextBuilderService. The resulting context later becomes
the input for LLM analysis, scoring, and career guidance.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "build_context"


class BuildContextNode:
    def __init__(self, builder: Any, event_publisher: Any | None = None):
        self._builder = builder
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        state.processing_context = self._builder.build(state)
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
