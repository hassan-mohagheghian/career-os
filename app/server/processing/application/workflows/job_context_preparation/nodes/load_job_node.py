"""LoadJobNode — loads Job information through the Jobs bounded context.

Uses JobService (JobRepository) — it does not access the database directly.
Emits the processing.loading_job event.
"""

from __future__ import annotations

from typing import Any

from processing.domain.workflow.job_data import JobData
from processing.domain.workflow.job_processing_state import JobProcessingState
from shared.infrastructure.events.processing_events import CONTEXT_LOADING_JOB


class LoadJobNode:
    def __init__(self, job_service: Any, event_publisher: Any | None = None):
        self._job_service = job_service
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        self._emit(state)
        try:
            job = self._job_service.get_job(state.job_id)
        except Exception as e:
            state.errors.append(f"Failed to load job {state.job_id}: {e}")
            return state

        if job is None:
            state.errors.append(f"Job {state.job_id} not found")
            return state

        state.job = JobData.from_job_dict(job)
        state.job_id = job.get("id") or state.job_id
        return state

    def _emit(self, state: JobProcessingState) -> None:
        if self._events is None:
            return
        self._events.publish(
            CONTEXT_LOADING_JOB,
            state.execution_id,
            state.job_id,
            "running",
            current_step="loading_job",
            message="Loading job information",
        )
