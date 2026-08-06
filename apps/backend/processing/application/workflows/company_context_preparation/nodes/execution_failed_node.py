"""ExecutionFailedNode — terminal node for an invalid company context."""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.company_processing_state import CompanyProcessingState


class ExecutionFailedNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        state.status = ExecutionStatus.FAILED
        progress_ops.mark_failed(self._events, state, "; ".join(state.errors))
        return state
