"""Tests for ProcessingQueueService snapshot entries (execution + job links)."""

import json
import uuid
from datetime import datetime, UTC

from processing.domain.enums import ExecutionStatus, ExecutionType
from processing.domain.entities.processing_execution import ProcessingExecution
from processing.application.services.processing_queue_service import ProcessingQueueService


class FakeExecutionRepo:
    def __init__(self, executions=None):
        self._store = {e.id: e for e in (executions or [])}

    def list_recent(self, limit: int = 200) -> list[ProcessingExecution]:
        return list(self._store.values())[:limit]


def _execution(status: ExecutionStatus, job_id: str = "job-1") -> ProcessingExecution:
    return ProcessingExecution(
        id=str(uuid.uuid4()),
        execution_type=ExecutionType.JOB_PROCESSING,
        target_type="job",
        target_id=job_id,
        status=status,
        created_at=datetime.now(UTC),
    )


class FakeJobRepo:
    def __init__(self, jobs: dict[str, dict]):
        self._jobs = jobs

    def get_by_id(self, job_id: str) -> dict | None:
        return self._jobs.get(job_id)


def _service(jobs: dict[str, dict], executions) -> ProcessingQueueService:
    return ProcessingQueueService(FakeExecutionRepo(executions), FakeJobRepo(jobs))


class TestProcessingQueueServiceSnapshot:
    def test_groups_by_status(self):
        service = _service(
            jobs={},
            executions=[
                _execution(ExecutionStatus.RUNNING),
                _execution(ExecutionStatus.QUEUED),
                _execution(ExecutionStatus.FAILED),
            ],
        )
        snapshot = service.snapshot()
        assert len(snapshot["processing"]) == 1
        assert len(snapshot["queued"]) == 1
        assert len(snapshot["failed"]) == 1

    def test_entry_includes_url_and_parsed_links_json_array(self):
        job_id = "job-1"
        jobs = {job_id: {"url": "https://example.com/jobs/1", "links": json.dumps([{"title": "Careers", "url": "https://example.com/careers"}])}}
        execution = _execution(ExecutionStatus.QUEUED, job_id=job_id)
        entry = _service(jobs, [execution]).snapshot()["queued"][0]
        assert entry["url"] == "https://example.com/jobs/1"
        assert entry["links"] == [{"title": "Careers", "url": "https://example.com/careers"}]

    def test_entry_parses_plain_string_links(self):
        job_id = "job-1"
        jobs = {job_id: {"url": None, "links": "https://example.com/careers"}}
        execution = _execution(ExecutionStatus.RUNNING, job_id=job_id)
        entry = _service(jobs, [execution]).snapshot()["processing"][0]
        assert entry["links"] == [{"url": "https://example.com/careers"}]

    def test_entry_parses_json_scalar_links(self):
        job_id = "job-1"
        jobs = {job_id: {"url": None, "links": json.dumps("https://example.com/careers")}}
        execution = _execution(ExecutionStatus.RUNNING, job_id=job_id)
        entry = _service(jobs, [execution]).snapshot()["processing"][0]
        assert entry["links"] == [{"url": "https://example.com/careers"}]

    def test_entry_returns_empty_links_without_job(self):
        execution = _execution(ExecutionStatus.RUNNING)
        entry = _service({}, [execution]).snapshot()["processing"][0]
        assert entry["url"] is None
        assert entry["links"] == []

    def test_entry_handles_non_json_links_gracefully(self):
        job_id = "job-1"
        jobs = {job_id: {"url": None, "links": "{not-json"}}
        execution = _execution(ExecutionStatus.RUNNING, job_id=job_id)
        entry = _service(jobs, [execution]).snapshot()["processing"][0]
        assert entry["links"] == [{"url": "{not-json"}]
