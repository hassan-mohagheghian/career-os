"""ProcessingQueueService — builds the Processing Queue snapshot.

The Processing Queue is a temporary execution view. It does not own Jobs; it
only reflects the current ProcessingExecution state (queued / running / failed)
so the frontend drawer can render it.

See docs/api/processing/get-processing-queue.md.
"""

from __future__ import annotations

from typing import Any

from processing.domain.enums import ExecutionStatus
from processing.domain.entities.processing_execution import ProcessingExecution
from processing.domain.repositories.processing_execution_repository import IProcessingExecutionRepository


class ProcessingQueueService:
    def __init__(self, execution_repository: IProcessingExecutionRepository, job_repository: Any = None):
        self._execution_repository = execution_repository
        self._job_repository = job_repository

    def snapshot(self, limit: int = 200) -> dict[str, list[dict[str, Any]]]:
        executions = self._execution_repository.list_recent(limit=limit)

        processing: list[dict[str, Any]] = []
        queued: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for execution in executions:
            entry = self._entry(execution)
            if execution.status in (ExecutionStatus.QUEUED, ExecutionStatus.STARTING):
                queued.append(entry)
            elif execution.status in (ExecutionStatus.RUNNING,):
                processing.append(entry)
            elif execution.status == ExecutionStatus.FAILED:
                failed.append(entry)

        processing.sort(key=lambda e: e.get("started_at") or "")
        failed.sort(key=lambda e: e.get("finished_at") or "", reverse=True)
        return {"processing": processing, "queued": queued, "failed": failed}

    def _entry(self, execution: ProcessingExecution) -> dict[str, Any]:
        progress = execution.workflow_progress or {}
        current_step = progress.get("current_step") or {}

        job = self._job(execution)

        return {
            "execution_id": execution.id,
            "job_id": execution.target_id if execution.target_type == "job" else execution.target_id,
            "title": self._job_title(job, execution),
            "status": execution.status.value,
            "current_step": current_step.get("title") or current_step.get("id"),
            "progress": progress.get("progress"),
            "error": execution.error_message,
            "failed_step": current_step.get("id"),
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "finished_at": execution.finished_at.isoformat() if execution.finished_at else None,
        }

    def _job(self, execution: ProcessingExecution):
        if self._job_repository is None or execution.target_type != "job":
            return None
        try:
            return self._job_repository.get_by_id(execution.target_id)
        except Exception:
            return None

    @staticmethod
    def _job_title(job, execution: ProcessingExecution) -> str:
        if job:
            return job.get("title") or job.get("role") or execution.target_id
        return execution.target_id
