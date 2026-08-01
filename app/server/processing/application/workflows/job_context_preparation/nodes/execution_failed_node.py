"""ExecutionFailedNode — terminal node for an invalid context."""

from __future__ import annotations

from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.job_processing_state import JobProcessingState


class ExecutionFailedNode:
    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        state.status = ExecutionStatus.FAILED
        return state
