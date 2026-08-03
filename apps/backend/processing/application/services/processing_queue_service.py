"""ProcessingQueueService — builds the Processing Queue snapshot.

The Processing Queue is a temporary execution view. It does not own Jobs; it
only reflects the current ProcessingExecution state (queued / running / failed)
so the frontend drawer can render it.

See docs/api/processing/get-processing-queue.md.
"""

from __future__ import annotations

import json
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
            "url": job.get("url") if job else None,
            "links": self._job_links(job) if job else [],
            "status": execution.status.value,
            "current_step": current_step.get("title") or current_step.get("id"),
            "progress": progress.get("progress"),
            "error": execution.error_message,
            "failed_step": current_step.get("id"),
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "finished_at": execution.finished_at.isoformat() if execution.finished_at else None,
        }

    @staticmethod
    def _job_links(job: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse a job's stored ``links`` value into link item dicts.

        Tolerates the formats produced over time: JSON arrays, JSON scalars and
        plain non-JSON strings (legacy worker). Plain strings are wrapped under
        ``url`` so they are never silently dropped.
        """
        raw = job.get("links")
        if not raw:
            return []
        if isinstance(raw, list):
            return [{"url": item} if isinstance(item, str) else item for item in raw]
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [{"url": item} if isinstance(item, str) else item for item in parsed]
                return [{"url": parsed} if isinstance(parsed, str) else parsed]
            except (TypeError, ValueError):
                return [{"url": raw}]
        return []

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
