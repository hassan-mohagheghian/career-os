"""CandidateReadyNode — terminal node for a completed candidate merge."""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.candidate_processing_state import CandidateProcessingState


class CandidateReadyNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: CandidateProcessingState) -> CandidateProcessingState:
        state.status = ExecutionStatus.COMPLETED
        progress_ops.finish_progress(self._events, state)
        return state
