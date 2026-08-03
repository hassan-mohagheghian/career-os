"""PersistContextNode — persists the prepared context to the job row.

Runs after validation succeeds and before context_ready. The prepared
combined_text is written to the job (raw_description + description) so the
analysis phase has a durable LLM input even though the in-memory workflow
context is not persisted. This node performs no LLM calls.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "persist_context"


class PersistContextNode:
    def __init__(self, job_service: Any, event_publisher: Any | None = None):
        self._job_service = job_service
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        context = state.processing_context
        if context is None or not context.combined_text:
            state.errors.append(f"[{NODE_ID}] No combined text to persist for {state.job_id}")
        else:
            try:
                self._job_service.persist_prepared_context(
                    state.job_id, context.combined_text
                )
            except Exception as e:
                state.errors.append(f"[{NODE_ID}] Failed to persist context: {e}")
                state.status = ExecutionStatus.FAILED
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
