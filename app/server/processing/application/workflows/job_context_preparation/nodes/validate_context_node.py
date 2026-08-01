"""ValidateContextNode — validates that enough information exists.

Valid: at least one meaningful content source exists.
Invalid: no extracted content, empty notes, or no usable source.

Delegates to JobContextValidatorService. Conditional edges route the
workflow to context_ready (valid) or execution_failed (invalid).
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.workflow.job_processing_context import JobProcessingContext
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "validate_context"


class ValidateContextNode:
    def __init__(self, validator: Any, event_publisher: Any | None = None):
        self._validator = validator
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        context = state.processing_context or JobProcessingContext(
            job_id=state.job_id,
            job=state.job,
        )
        state.processing_context = context
        result = self._validator.validate(context)
        state.validation_result = result
        if not result.valid:
            state.errors.extend(result.reasons)
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
