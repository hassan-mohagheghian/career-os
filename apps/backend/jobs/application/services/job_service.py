"""JobService — application service for loading Job information.

The Job Context bounded context owns Job loading. The processing workflow
depends on this service (via the Job repository) rather than accessing the
database directly from workflow nodes.
"""

from __future__ import annotations

from typing import Any

from jobs.domain.repositories.job_repository import IJobRepository
from shared.application.exceptions import NotFoundError


class JobService:
    def __init__(self, repository: IJobRepository):
        self._repository = repository

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Load a job by its UUID."""
        return self._repository.get_by_id(job_id)

    def get_job_or_raise(self, job_id: str) -> dict[str, Any]:
        job = self.get_job(job_id)
        if not job:
            raise NotFoundError(f"Job {job_id} not found")
        return job

    def persist_prepared_context(
        self, job_id: str, combined_text: str, easy_apply: bool | None = None
    ) -> None:
        """Persist the prepared context so it survives the in-memory pipeline.

        The analysis phase reads this text as its durable LLM input. Stored on
        the job as both raw_description (the raw fetched/extracted text) and
        description (the user-facing field).
        """
        fields: dict[str, Any] = {
            "raw_description": combined_text,
            "description": combined_text,
        }
        if easy_apply is not None:
            fields["easy_apply"] = int(easy_apply)
        self._repository.update_fields(job_id, **fields)
