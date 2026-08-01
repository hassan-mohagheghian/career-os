"""Extra tests for shared.infrastructure.process.repository.

Covers PendingJobRepository / PendingCompanyRepository / JobRepository
branches not exercised by the existing suite: not-found paths, ItemStatus
and string statuses, update_fields, append_log/get_logs on companies,
reset_orphans (both branches), insert/insert_summary/insert_resume
(new + existing), save_workflow_log, and the dict helpers.
"""

import json

import pytest

from jobs.infrastructure.models.job_model import JobModel
from companies.infrastructure.models.company_model import CompanyModel
from shared.infrastructure.database.models.misc_models import SummaryModel, ResumeModel
from shared.infrastructure.process.repository import (
    PendingJobRepository,
    PendingCompanyRepository,
    JobRepository,
)
from shared.infrastructure.process.models import ItemStatus, WorkflowLogEntry


def _job(sa_session, **kwargs):
    defaults = {"url": "https://example.com/j", "status": "queued"}
    defaults.update(kwargs)
    m = JobModel(**defaults)
    sa_session.add(m)
    sa_session.commit()
    sa_session.refresh(m)
    return m


def _company(sa_session, **kwargs):
    defaults = {"name": "Corp", "status": "queued"}
    defaults.update(kwargs)
    m = CompanyModel(**defaults)
    sa_session.add(m)
    sa_session.commit()
    sa_session.refresh(m)
    return m


class TestPendingJobRepository:
    def test_get_returns_full_dict(self, sa_session):
        m = _job(sa_session, num=7, source="cli", status="queued",
                 notes="[]", links="[]", workflow_log="[]", company="Acme")
        repo = PendingJobRepository(sa_session)
        item = repo.get(m.num)
        assert item["id"] == 7
        assert item["num"] == 7
        assert item["job_num"] == 7
        assert item["source"] == "cli"
        assert item["company"] == "Acme"

    def test_update_status_with_enum(self, sa_session):
        m = _job(sa_session)
        repo = PendingJobRepository(sa_session)
        repo.update_status(m.num, ItemStatus.PROCESSING, error="e")
        row = sa_session.query(JobModel).filter(JobModel.num == m.num).first()
        assert row.status == "processing"
        assert row.error == "e"

    def test_update_status_with_string(self, sa_session):
        m = _job(sa_session)
        repo = PendingJobRepository(sa_session)
        repo.update_status(m.num, "failed")
        row = sa_session.query(JobModel).filter(JobModel.num == m.num).first()
        assert row.status == "failed"

    def test_update_status_not_found(self, sa_session):
        repo = PendingJobRepository(sa_session)
        repo.update_status(999, "failed")  # should not raise

    def test_update_fields(self, sa_session):
        m = _job(sa_session)
        repo = PendingJobRepository(sa_session)
        repo.update_fields(m.num, table="pending_jobs", notes="[1]")
        row = sa_session.query(JobModel).filter(JobModel.num == m.num).first()
        assert row.notes == "[1]"

    def test_update_fields_not_found(self, sa_session):
        repo = PendingJobRepository(sa_session)
        repo.update_fields(999, notes="[1]")

    def test_update_step_not_found(self, sa_session):
        repo = PendingJobRepository(sa_session)
        repo.update_step(999, "progress_pct", 50)

    def test_update_step_with_extra_fields(self, sa_session):
        m = _job(sa_session)
        repo = PendingJobRepository(sa_session)
        repo.update_step(m.num, "progress_pct", 55, error="x")
        row = sa_session.query(JobModel).filter(JobModel.num == m.num).first()
        assert row.progress_pct == 55
        assert row.error == "x"

    def test_append_log_not_found(self, sa_session):
        repo = PendingJobRepository(sa_session)
        repo.append_log(999, WorkflowLogEntry(step="s", msg="m"))

    def test_get_logs_empty(self, sa_session):
        m = _job(sa_session)
        repo = PendingJobRepository(sa_session)
        assert repo.get_logs(m.num) == []

    def test_get_logs_with_entries(self, sa_session):
        m = _job(sa_session, workflow_log='[{"step": "fetch", "msg": "done", "ts": "10:00"}]')
        repo = PendingJobRepository(sa_session)
        logs = repo.get_logs(m.num)
        assert len(logs) == 1
        assert logs[0].step == "fetch"
        assert logs[0].msg == "done"

    def test_get_logs_not_found(self, sa_session):
        repo = PendingJobRepository(sa_session)
        assert repo.get_logs(999) == []

    def test_reset_orphans_count_zero(self, sa_session):
        _job(sa_session, status="queued")
        repo = PendingJobRepository(sa_session)
        assert repo.reset_orphans() == 0

    def test_reset_orphans_requeues(self, sa_session):
        m = _job(sa_session, status="processing", error="oops")
        repo = PendingJobRepository(sa_session)
        assert repo.reset_orphans() == 1
        row = sa_session.query(JobModel).filter(JobModel.num == m.num).first()
        assert row.status == "queued"
        assert row.error is None

    def test_claim_next_sets_status(self, sa_session):
        m = _job(sa_session, status="queued")
        repo = PendingJobRepository(sa_session)
        claimed = repo.claim_next()
        assert claimed["num"] == m.num
        row = sa_session.query(JobModel).filter(JobModel.num == m.num).first()
        assert row.status == "processing"


class TestPendingCompanyRepository:
    def test_get_found_and_not_found(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        item = repo.get(c.id)
        assert item["id"] == c.id
        assert item["company_id"] == c.id
        assert item["input_text"] == "[]"
        assert repo.get(999) is None

    def test_update_status_enum(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        repo.update_status(c.id, ItemStatus.PROCESSING)
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.status == "processing"

    def test_update_status_string_not_found(self, sa_session):
        repo = PendingCompanyRepository(sa_session)
        repo.update_status(999, "failed")

    def test_update_status_with_extra_fields(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        repo.update_status(c.id, ItemStatus.PROCESSING, current_node="fetch", error="e")
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.status == "processing"
        assert row.current_node == "fetch"
        assert row.error == "e"

    def test_update_fields(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        repo.update_fields(c.id, table="pending_companies", error="x")
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.error == "x"

    def test_update_fields_not_found(self, sa_session):
        repo = PendingCompanyRepository(sa_session)
        repo.update_fields(999, error="x")

    def test_update_step(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        repo.update_step(c.id, "progress_pct", 33)
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.progress_pct == 33

    def test_update_step_not_found(self, sa_session):
        repo = PendingCompanyRepository(sa_session)
        repo.update_step(999, "progress_pct", 33)

    def test_update_step_with_extra_fields(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        repo.update_step(c.id, "progress_pct", 44, current_node="analyze")
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.progress_pct == 44
        assert row.current_node == "analyze"

    def test_append_log_and_get_logs(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        repo.append_log(c.id, WorkflowLogEntry(step="fetch", msg="ok", ts="09:00"))
        logs = repo.get_logs(c.id)
        assert len(logs) == 1
        assert logs[0].step == "fetch"

    def test_append_log_not_found(self, sa_session):
        repo = PendingCompanyRepository(sa_session)
        repo.append_log(999, WorkflowLogEntry(step="s", msg="m"))

    def test_get_logs_empty_and_not_found(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        assert repo.get_logs(c.id) == []
        assert repo.get_logs(999) == []

    def test_claim_next(self, sa_session):
        c = _company(sa_session, status="queued")
        repo = PendingCompanyRepository(sa_session)
        claimed = repo.claim_next()
        assert claimed["id"] == c.id
        assert claimed["status"] == "processing"

    def test_claim_next_none(self, sa_session):
        repo = PendingCompanyRepository(sa_session)
        assert repo.claim_next() is None

    def test_count_by_status(self, sa_session):
        _company(sa_session, status="processing")
        _company(sa_session, status="queued")
        repo = PendingCompanyRepository(sa_session)
        counts = repo.count_by_status()
        assert counts["processing"] == 1
        assert counts["queued"] == 1
        assert counts["created"] == 0

    def test_reset_orphans_zero(self, sa_session):
        _company(sa_session, status="queued")
        repo = PendingCompanyRepository(sa_session)
        assert repo.reset_orphans() == 0

    def test_reset_orphans_resets(self, sa_session):
        c = _company(sa_session, status="processing", error="x")
        repo = PendingCompanyRepository(sa_session)
        assert repo.reset_orphans() == 1
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.status == "created"
        assert row.error is None


class TestJobRepository:
    def test_insert_new_raises(self, sa_session):
        """The new-job branch passes posted_at (invalid kwarg) and raises."""
        repo = JobRepository(sa_session)
        with pytest.raises(TypeError):
            repo.insert({
                "num": 1, "url": "https://x.com", "company": "Acme",
                "role": "Eng", "location": "Berlin", "locations": ["Berlin"],
                "work_types": ["Remote"], "stack": "Python", "salary": "100k",
                "match": "High", "score": "A", "employment_type": "Full-time",
                "work_type": "Remote", "overall_score": 80,
            })

    def test_insert_existing_updates(self, sa_session):
        _job(sa_session, num=1, company="Old")
        repo = JobRepository(sa_session)
        repo.insert({"num": 1, "company": "New", "score": "A+"})
        row = sa_session.query(JobModel).filter(JobModel.num == 1).first()
        assert row.company == "New"
        assert row.score == "A+"

    def test_get_by_url_not_found(self, sa_session):
        repo = JobRepository(sa_session)
        assert repo.get_by_url("https://missing.com") is None

    def test_get_by_url_found(self, sa_session):
        _job(sa_session, num=1, url="https://x.com", company="Acme", score="A")
        repo = JobRepository(sa_session)
        job = repo.get_by_url("https://x.com")
        assert job["num"] == 1
        assert job["match"] is None

    def test_insert_summary_new_raises(self, sa_session):
        """The new-summary branch passes resume_fit (invalid kwarg) and raises."""
        repo = JobRepository(sa_session)
        with pytest.raises(TypeError):
            repo.insert_summary({"num": 1, "company": "Acme", "summary": "Great"})

    def test_insert_summary_existing(self, sa_session):
        sa_session.add(SummaryModel(num=1, company="Old"))
        sa_session.commit()
        repo = JobRepository(sa_session)
        repo.insert_summary({"num": 1, "company": "New"})
        row = sa_session.query(SummaryModel).filter(SummaryModel.num == 1).first()
        assert row.company == "New"

    def test_insert_resume_new(self, sa_session):
        repo = JobRepository(sa_session)
        repo.insert_resume({"id": "pending_1", "title": "T", "company": "A",
                            "role": "R", "content": "C", "version": 1,
                            "raw_text": "RT", "job_num": 1})
        row = sa_session.query(ResumeModel).filter(ResumeModel.id == "pending_1").first()
        assert row is not None
        assert row.company == "A"

    def test_insert_resume_existing(self, sa_session):
        sa_session.add(ResumeModel(id="pending_1", title="Old", version=1))
        sa_session.commit()
        repo = JobRepository(sa_session)
        repo.insert_resume({"id": "pending_1", "title": "New", "version": 2})
        row = sa_session.query(ResumeModel).filter(ResumeModel.id == "pending_1").first()
        assert row.title == "New"
        assert row.version == 2

    def test_save_workflow_log(self, sa_session):
        m = _job(sa_session, num=1)
        repo = JobRepository(sa_session)
        repo.save_workflow_log(m.num, '["x"]')
        row = sa_session.query(JobModel).filter(JobModel.num == m.num).first()
        assert row.workflow_log == '["x"]'

    def test_save_workflow_log_not_found(self, sa_session):
        repo = JobRepository(sa_session)
        repo.save_workflow_log(999, '["x"]')
