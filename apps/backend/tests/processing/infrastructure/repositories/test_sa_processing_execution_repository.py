"""Tests for SQLAlchemyProcessingExecutionRepository list projection helpers.

Covers:
- latest_by_target_ids: batch latest-execution lookup for the jobs list.
- target_ids_with_status: ids whose latest execution has a given status.

A dedicated ``target_type`` is used so tests stay isolated from executions
created by other test files in the same (session-scoped) database.
"""

import uuid

import pytest

from processing.infrastructure.models.processing_execution_model import ProcessingExecutionModel
from processing.infrastructure.repositories.sa_processing_execution_repository import (
    SQLAlchemyProcessingExecutionRepository,
)

TARGET_TYPE = "test_target"

_counter = iter(range(1, 100))


@pytest.fixture(autouse=True)
def _clean_target_type(sa_session):
    sa_session.query(ProcessingExecutionModel).filter(
        ProcessingExecutionModel.target_type == TARGET_TYPE
    ).delete(synchronize_session=False)
    sa_session.commit()
    yield


def _add_execution(sa_session, target_id: str, status: str, execution_id: str | None = None):
    created_at = f"2026-08-01T10:00:{next(_counter):02d}.000Z"
    model = ProcessingExecutionModel(
        id=execution_id or str(uuid.uuid7()),
        execution_type="job_processing",
        status=status,
        target_type=TARGET_TYPE,
        target_id=target_id,
        created_at=created_at,
        started_at=created_at,
        finished_at=None,
    )
    sa_session.add(model)
    sa_session.commit()
    return model


def _repo(sa_session) -> SQLAlchemyProcessingExecutionRepository:
    return SQLAlchemyProcessingExecutionRepository(sa_session)


class TestLatestByTargetIds:
    def test_returns_latest_execution_per_target(self, sa_session):
        _add_execution(sa_session, "job-a", status="failed", execution_id="a-1")
        _add_execution(sa_session, "job-a", status="completed", execution_id="a-2")
        _add_execution(sa_session, "job-b", status="queued", execution_id="b-1")

        latest = _repo(sa_session).latest_by_target_ids(TARGET_TYPE, ["job-a", "job-b"])

        assert set(latest) == {"job-a", "job-b"}
        assert latest["job-a"]["id"] == "a-2"
        assert latest["job-a"]["status"] == "completed"
        assert latest["job-b"]["status"] == "queued"

    def test_empty_ids_returns_empty(self, sa_session):
        assert _repo(sa_session).latest_by_target_ids(TARGET_TYPE, []) == {}

    def test_missing_targets_are_omitted(self, sa_session):
        _add_execution(sa_session, "job-a", status="completed", execution_id="a-1")
        latest = _repo(sa_session).latest_by_target_ids(TARGET_TYPE, ["job-a", "missing"])
        assert set(latest) == {"job-a"}


class TestTargetIdsWithStatus:
    def test_matches_latest_status_only(self, sa_session):
        _add_execution(sa_session, "job-a", status="failed", execution_id="a-1")
        _add_execution(sa_session, "job-a", status="completed", execution_id="a-2")
        _add_execution(sa_session, "job-b", status="completed", execution_id="b-1")

        assert _repo(sa_session).target_ids_with_status(TARGET_TYPE, "completed") == {"job-a", "job-b"}
        assert _repo(sa_session).target_ids_with_status(TARGET_TYPE, "failed") == set()

    def test_ignores_other_target_types(self, sa_session):
        _add_execution(sa_session, "job-a", status="completed", execution_id="a-1")
        other = ProcessingExecutionModel(
            id=str(uuid.uuid7()),
            execution_type="company_processing",
            status="completed",
            target_type="other_type",
            target_id="job-a",
        )
        sa_session.add(other)
        sa_session.commit()

        assert _repo(sa_session).target_ids_with_status(TARGET_TYPE, "completed") == {"job-a"}
