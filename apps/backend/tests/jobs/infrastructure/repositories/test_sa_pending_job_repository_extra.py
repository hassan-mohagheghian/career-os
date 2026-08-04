"""Extra tests for SQLAlchemyPendingJobRepository.

Covers branch combinations for pending_jobs (JobModel): update_status with
extra fields, update_status not-found, create with notes/links, create
existing URL reset, get_pending_count, mark_processing_as_waiting,
get_by_url_pending, delete paths, and direct create.
"""

import json

import pytest

from jobs.infrastructure.models.job_model import JobModel
from jobs.infrastructure.repositories.sa_pending_job_repository import SQLAlchemyPendingJobRepository


@pytest.fixture
def repo(sa_session):
    return SQLAlchemyPendingJobRepository(sa_session)


def _job(sa_session, **kwargs):
    defaults = {"url": "https://example.com/j", "deleted": 0}
    defaults.update(kwargs)
    m = JobModel(**defaults)
    sa_session.add(m)
    sa_session.commit()
    sa_session.refresh(m)
    return m


class TestUpdateStatus:
    def test_update_status_with_extra_fields(self, sa_session, repo):
        j = _job(sa_session, status="queued")
        assert repo.update_status(j.id, "processing", table="pending_jobs",
                                  error="x", session_id="s1") is True
        row = sa_session.query(JobModel).filter(JobModel.id == j.id).first()
        assert row.status == "processing"
        assert row.error == "x"
        assert row.session_id == "s1"

    def test_update_status_not_found(self, repo):
        assert repo.update_status("999", "processing", table="pending_jobs") is False


class TestCreate:
    def test_create_job_with_notes_and_links(self, sa_session, repo):
        result = repo.create({
            "url": "https://example.com/new",
            "source": "api",
            "company": "Acme",
            "notes": [{"a": 1}],
            "links": ["https://l.com"],
        }, "pending_jobs")
        assert result["url"] == "https://example.com/new"
        assert json.loads(result["notes"]) == [{"a": 1}]
        assert result["status"] == "created"
        row = sa_session.query(JobModel).filter(JobModel.id == result["id"]).first()
        assert json.loads(row.links) == ["https://l.com"]
        assert row.company == "Acme"

    def test_create_job_existing_resets_workflow(self, sa_session, repo):
        _job(sa_session, url="https://example.com/dup", status="failed", error="boom")
        result = repo.create({"url": "https://example.com/dup", "source": "api"}, "pending_jobs")
        assert result["status"] == "created"
        assert result["error"] is None
        assert result["workflow_log"] == "[]"


class TestCounts:
    def test_get_pending_count_jobs(self, sa_session, repo):
        _job(sa_session, status="pending")
        _job(sa_session, status="processing")
        assert repo.get_pending_count("pending_jobs") == 1


class TestProcessingHelpers:
    def test_mark_processing_as_waiting_jobs(self, sa_session, repo):
        _job(sa_session, status="processing")
        _job(sa_session, status="queued")
        count = repo.mark_processing_as_waiting("pending_jobs")
        assert count == 1
        row = sa_session.query(JobModel).filter(JobModel.status == "processing").first()
        assert row is None


class TestStreamAndDelete:
    def test_get_by_url_pending_not_found(self, repo):
        assert repo.get_by_url_pending("https://missing.com") is None

    def test_delete_job_not_found(self, repo):
        assert repo.delete("999", "pending_jobs") is False

    def test_delete_job_found(self, sa_session, repo):
        j = _job(sa_session)
        assert repo.delete(j.id, "pending_jobs") is True
        row = sa_session.query(JobModel).filter(JobModel.id == j.id).first()
        assert row.deleted == 1

    def test_create_pending_job_direct(self, repo):
        result = repo.create_pending_job("https://example.com/direct", "api", "Acme", "pending")
        assert result["url"] == "https://example.com/direct"
        assert result["status"] == "pending"
        assert result["company"] == "Acme"
