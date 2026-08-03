"""Extra tests for SQLAlchemyPendingRepository.

Covers branch combinations across BOTH pending_jobs (JobModel) and
pending_companies (CompanyModel): update_status with extra fields,
update_status not-found, get_pending_count, company count variants,
mark_processing_as_waiting / reset_processing_orphans company + unknown,
get_queued_items companies, delete paths, create with notes/links, and
unknown-table fallbacks.
"""

import json

import pytest

from jobs.infrastructure.models.job_model import JobModel
from companies.infrastructure.models.company_model import CompanyModel
from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository


@pytest.fixture
def repo(sa_session):
    return SQLAlchemyPendingRepository(sa_session)


def _job(sa_session, **kwargs):
    defaults = {"url": "https://example.com/j", "deleted": 0}
    defaults.update(kwargs)
    m = JobModel(**defaults)
    sa_session.add(m)
    sa_session.commit()
    sa_session.refresh(m)
    return m


def _company(sa_session, **kwargs):
    defaults = {"name": "Corp"}
    defaults.update(kwargs)
    m = CompanyModel(**defaults)
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

    def test_update_status_company(self, sa_session, repo):
        c = _company(sa_session, status="queued")
        assert repo.update_status(str(c.id), "processing", table="pending_companies") is True
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.status == "processing"

    def test_update_status_not_found(self, repo):
        assert repo.update_status("999", "processing", table="pending_jobs") is False

    def test_update_status_unknown_table(self, sa_session, repo):
        _job(sa_session)
        assert repo.update_status("1", "processing", table="bogus") is False

    def test_update_status_company_not_found(self, repo):
        assert repo.update_status("999", "processing", table="pending_companies") is False


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

    def test_create_company_with_notes(self, sa_session, repo):
        result = repo.create({"notes": [1, 2]}, "pending_companies")
        assert result["status"] == "created"
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == result["id"]).first()
        assert json.loads(row.notes) == [1, 2]

    def test_create_unknown_table(self, repo):
        with pytest.raises(ValueError):
            repo.create({}, "bogus")


class TestCounts:
    def test_get_pending_count_jobs(self, sa_session, repo):
        _job(sa_session, status="pending")
        _job(sa_session, status="processing")
        assert repo.get_pending_count("pending_jobs") == 1

    def test_get_pending_count_companies(self, sa_session, repo):
        _company(sa_session, status="pending")
        _company(sa_session, status="created")
        assert repo.get_pending_count("pending_companies") == 1

    def test_get_pending_count_unknown(self, repo):
        assert repo.get_pending_count("bogus") == 0

    def test_get_processing_count_companies(self, sa_session, repo):
        _company(sa_session, status="processing")
        _company(sa_session, status="queued")
        assert repo.get_processing_count("pending_companies") == 1

    def test_get_processing_count_unknown(self, repo):
        assert repo.get_processing_count("bogus") == 0

    def test_get_queued_count_companies(self, sa_session, repo):
        _company(sa_session, status="queued")
        _company(sa_session, status="pending")
        assert repo.get_queued_count("pending_companies") == 1

    def test_get_queued_count_unknown(self, repo):
        assert repo.get_queued_count("bogus") == 0

    def test_get_max_queue_order_unknown(self, repo):
        assert repo.get_max_queue_order("bogus") == 0

    def test_count_pending_unknown(self, repo):
        assert repo.count_pending("bogus") == 0


class TestProcessingHelpers:
    def test_get_processing_items_companies(self, sa_session, repo):
        c = _company(sa_session, status="processing")
        _company(sa_session, status="queued")
        items = repo.get_processing_items("pending_companies")
        assert len(items) == 1
        assert items[0]["id"] == c.id

    def test_get_processing_items_unknown(self, repo):
        assert repo.get_processing_items("bogus") == []

    def test_mark_processing_as_waiting_jobs(self, sa_session, repo):
        _job(sa_session, status="processing")
        _job(sa_session, status="queued")
        count = repo.mark_processing_as_waiting("pending_jobs")
        assert count == 1
        row = sa_session.query(JobModel).filter(JobModel.status == "processing").first()
        assert row is None

    def test_mark_processing_as_waiting_companies(self, sa_session, repo):
        _company(sa_session, status="processing")
        count = repo.mark_processing_as_waiting("pending_companies")
        assert count == 1
        row = sa_session.query(CompanyModel).filter(CompanyModel.status == "processing").first()
        assert row is None

    def test_mark_processing_as_waiting_unknown(self, repo):
        assert repo.mark_processing_as_waiting("bogus") == 0

    def test_reset_processing_orphans_companies(self, sa_session, repo):
        _company(sa_session, status="processing")
        _company(sa_session, status="queued")
        count = repo.reset_processing_orphans("pending_companies")
        assert count == 1
        row = sa_session.query(CompanyModel).filter(CompanyModel.status == "created").first()
        assert row is not None

    def test_reset_processing_orphans_unknown(self, repo):
        assert repo.reset_processing_orphans("bogus") == 0


class TestQueuedItems:
    def test_get_queued_items_companies(self, sa_session, repo):
        c = _company(sa_session, status="queued")
        _company(sa_session, status="pending")
        items = repo.get_queued_items("pending_companies")
        assert len(items) == 1
        assert items[0]["id"] == c.id

    def test_get_queued_items_unknown(self, repo):
        assert repo.get_queued_items("bogus") == []

    def test_pick_queued_item_unknown_table(self, sa_session, repo):
        _job(sa_session, status="queued")
        assert repo.pick_queued_item("bogus") is None


class TestStreamAndDelete:
    def test_get_all_for_stream_companies(self, sa_session, repo):
        c = _company(sa_session, status="pending")
        rows = repo.get_all_for_stream("pending_companies")
        assert len(rows) == 1
        assert rows[0]["id"] == c.id

    def test_get_all_for_stream_unknown(self, repo):
        assert repo.get_all_for_stream("bogus") == []

    def test_get_by_url_pending_not_found(self, repo):
        assert repo.get_by_url_pending("https://missing.com") is None

    def test_delete_job_not_found(self, repo):
        assert repo.delete("999", "pending_jobs") is False

    def test_delete_job_found(self, sa_session, repo):
        j = _job(sa_session)
        assert repo.delete(j.id, "pending_jobs") is True
        row = sa_session.query(JobModel).filter(JobModel.id == j.id).first()
        assert row.deleted == 1

    def test_delete_company_found(self, sa_session, repo):
        c = _company(sa_session)
        assert repo.delete(c.id, "pending_companies") is True
        assert sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first() is None

    def test_delete_company_not_found(self, repo):
        assert repo.delete(999, "pending_companies") is False

    def test_delete_unknown_table(self, repo):
        assert repo.delete(1, "bogus") is False

    def test_create_pending_company(self, repo):
        result = repo.create_pending_company("SomeCo", "url", "web", "created", "[]")
        assert result["status"] == "created"

    def test_create_pending_job_direct(self, repo):
        result = repo.create_pending_job("https://example.com/direct", "api", "Acme", "pending")
        assert result["url"] == "https://example.com/direct"
        assert result["status"] == "pending"
        assert result["company"] == "Acme"

    def test_update_step_company(self, sa_session, repo):
        c = _company(sa_session)
        assert repo.update_step(c.id, "progress_pct", 50, table="pending_companies") is True
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.progress_pct == 50

    def test_update_workflow_log_company(self, sa_session, repo):
        c = _company(sa_session)
        assert repo.update_workflow_log(c.id, '["a"]', table="pending_companies") is True
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.workflow_log == '["a"]'
