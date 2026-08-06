"""AnalysisReadyNode — terminal node for a completed company analysis."""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.company_processing_state import CompanyProcessingState


class AnalysisReadyNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        state.status = ExecutionStatus.COMPLETED
        progress_ops.finish_progress(self._events, state)
        return state
