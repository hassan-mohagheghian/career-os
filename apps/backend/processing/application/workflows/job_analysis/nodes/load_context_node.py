"""LoadContextNode — rebuilds the analysis context for a job.

The analysis graph runs after context preparation. It loads the job from the
Jobs bounded context (the prepared context was persisted to the job row by the
prep phase) and rebuilds a JobProcessingContext as the LLM input.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.job_data import JobData
from processing.domain.workflow.job_processing_context import JobProcessingContext
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "load_context"


class LoadContextNode:
    def __init__(self, job_service: Any, event_publisher: Any | None = None):
        self._job_service = job_service
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        try:
            job = self._job_service.get_job(state.job_id)
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to load job {state.job_id}: {e}")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        if job is None:
            state.errors.append(f"[{NODE_ID}] Job {state.job_id} not found")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        state.job = JobData.from_job_dict(job)
        job_text = job.get("raw_description") or job.get("description") or ""
        if not job_text:
            state.errors.append(f"[{NODE_ID}] Job {state.job_id} has no prepared content")
            state.status = ExecutionStatus.FAILED
        state.processing_context = JobProcessingContext(
            job_id=state.job_id,
            job=state.job,
            combined_text=job_text,
        )
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
