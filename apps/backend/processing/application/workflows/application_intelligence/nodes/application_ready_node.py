"""ApplicationReadyNode — terminal node for a completed generation."""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.application_intelligence_state import (
    ApplicationIntelligenceState,
)


class ApplicationReadyNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: ApplicationIntelligenceState) -> ApplicationIntelligenceState:
        state.status = ExecutionStatus.COMPLETED
        progress_ops.finish_progress(self._events, state)
        return state
