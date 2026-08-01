"""LoadJobNode — loads Job information through the Jobs bounded context.

Uses JobService (JobRepository) — it does not access the database directly.
Emits workflow.step.started/completed events and updates the WorkflowProgress
tree for the load_job step.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.workflow.job_data import JobData
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "load_job"


class LoadJobNode:
    def __init__(self, job_service: Any, event_publisher: Any | None = None):
        self._job_service = job_service
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        try:
            job = self._job_service.get_job(state.job_id)
        except Exception as e:
            state.errors.append(f"Failed to load job {state.job_id}: {e}")
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        if job is None:
            state.errors.append(f"Job {state.job_id} not found")
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        state.job = JobData.from_job_dict(job)
        state.job_id = job.get("id") or state.job_id
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
