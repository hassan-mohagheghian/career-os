"""ContextReadyNode — terminal node for a valid context."""

from __future__ import annotations

from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.job_processing_state import JobProcessingState


class ContextReadyNode:
    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        state.status = ExecutionStatus.COMPLETED
        return state
