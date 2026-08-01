"""BuildContextNode — creates the final JobProcessingContext.

Delegates to JobContextBuilderService. The resulting context later becomes
the input for LLM analysis, scoring, and career guidance.
"""

from __future__ import annotations

from typing import Any

from processing.domain.workflow.job_processing_state import JobProcessingState


class BuildContextNode:
    def __init__(self, builder: Any):
        self._builder = builder

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        state.processing_context = self._builder.build(state)
        return state
