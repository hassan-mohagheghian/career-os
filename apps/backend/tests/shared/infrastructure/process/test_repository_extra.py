"""Extra tests for shared.infrastructure.process.repository.

Covers PendingJobRepository / PendingCompanyRepository branches not
exercised by the existing suite: not-found paths, ItemStatus and string
statuses, update_fields, append_log/get_logs on companies, reset_orphans
(both branches), and the dict helpers.
"""

import json
import uuid

import pytest

from jobs.infrastructure.models.job_model import JobModel
from companies.infrastructure.models.company_model import CompanyModel
from shared.infrastructure.process.repository import (
    PendingJobRepository,
    PendingCompanyRepository,
)
from shared.infrastructure.process.models import ItemStatus, WorkflowLogEntry


def _job(sa_session, **kwargs):
    defaults = {"id": str(uuid.uuid7()), "url": "https://example.com/j", "status": "queued"}
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
        m = _job(sa_session, source="cli", status="queued",
                 notes="[]", links="[]", workflow_log="[]", company="Acme")
        repo = PendingJobRepository(sa_session)
        item = repo.get(m.id)
        assert item["id"] == m.id
        assert item["job_id"] == m.id
        assert item["source"] == "cli"
        assert item["company"] == "Acme"

    def test_update_status_with_enum(self, sa_session):
        m = _job(sa_session)
        repo = PendingJobRepository(sa_session)
        repo.update_status(m.id, ItemStatus.PROCESSING, error="e")
        row = sa_session.query(JobModel).filter(JobModel.id == m.id).first()
        assert row.status == "processing"
        assert row.error == "e"

    def test_update_status_with_string(self, sa_session):
        m = _job(sa_session)
        repo = PendingJobRepository(sa_session)
        repo.update_status(m.id, "failed")
        row = sa_session.query(JobModel).filter(JobModel.id == m.id).first()
        assert row.status == "failed"

    def test_update_status_not_found(self, sa_session):
        repo = PendingJobRepository(sa_session)
        repo.update_status("999", "failed")  # should not raise

    def test_update_fields(self, sa_session):
        m = _job(sa_session)
        repo = PendingJobRepository(sa_session)
        repo.update_fields(m.id, table="pending_jobs", notes="[1]")
        row = sa_session.query(JobModel).filter(JobModel.id == m.id).first()
        assert row.notes == "[1]"

    def test_update_fields_not_found(self, sa_session):
        repo = PendingJobRepository(sa_session)
        repo.update_fields("999", notes="[1]")

    def test_update_step_not_found(self, sa_session):
        repo = PendingJobRepository(sa_session)
        repo.update_step("999", "progress_pct", 50)

    def test_update_step_with_extra_fields(self, sa_session):
        m = _job(sa_session)
        repo = PendingJobRepository(sa_session)
        repo.update_step(m.id, "progress_pct", 55, error="x")
        row = sa_session.query(JobModel).filter(JobModel.id == m.id).first()
        assert row.progress_pct == 55
        assert row.error == "x"

    def test_append_log_not_found(self, sa_session):
        repo = PendingJobRepository(sa_session)
        repo.append_log("999", WorkflowLogEntry(step="s", msg="m"))

    def test_get_logs_empty(self, sa_session):
        m = _job(sa_session)
        repo = PendingJobRepository(sa_session)
        assert repo.get_logs(m.id) == []

    def test_get_logs_with_entries(self, sa_session):
        m = _job(sa_session, workflow_log='[{"step": "fetch", "msg": "done", "ts": "10:00"}]')
        repo = PendingJobRepository(sa_session)
        logs = repo.get_logs(m.id)
        assert len(logs) == 1
        assert logs[0].step == "fetch"
        assert logs[0].msg == "done"

    def test_get_logs_not_found(self, sa_session):
        repo = PendingJobRepository(sa_session)
        assert repo.get_logs("999") == []

    def test_reset_orphans_count_zero(self, sa_session):
        _job(sa_session, status="queued")
        repo = PendingJobRepository(sa_session)
        assert repo.reset_orphans() == 0

    def test_reset_orphans_requeues(self, sa_session):
        m = _job(sa_session, status="processing", error="oops")
        repo = PendingJobRepository(sa_session)
        assert repo.reset_orphans() == 1
        row = sa_session.query(JobModel).filter(JobModel.id == m.id).first()
        assert row.status == "queued"
        assert row.error is None

    def test_claim_next_sets_status(self, sa_session):
        m = _job(sa_session, status="queued")
        repo = PendingJobRepository(sa_session)
        claimed = repo.claim_next()
        assert claimed["id"] == m.id
        row = sa_session.query(JobModel).filter(JobModel.id == m.id).first()
        assert row.status == "processing"


class TestPendingCompanyRepository:
    def test_get_found_and_not_found(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        item = repo.get(c.id)
        assert item["id"] == c.id
        assert item["company_id"] == c.id
        assert item["input_text"] == "[]"
        assert repo.get("00000000-0000-0000-0000-000000000000") is None

    def test_update_status_enum(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        repo.update_status(c.id, ItemStatus.PROCESSING)
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.status == "processing"

    def test_update_status_string_not_found(self, sa_session):
        repo = PendingCompanyRepository(sa_session)
        repo.update_status("00000000-0000-0000-0000-000000000000", "failed")

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
        repo.update_fields("00000000-0000-0000-0000-000000000000", error="x")

    def test_update_step(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        repo.update_step(c.id, "progress_pct", 33)
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.progress_pct == 33

    def test_update_step_not_found(self, sa_session):
        repo = PendingCompanyRepository(sa_session)
        repo.update_step("00000000-0000-0000-0000-000000000000", "progress_pct", 33)

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
        repo.append_log("00000000-0000-0000-0000-000000000000", WorkflowLogEntry(step="s", msg="m"))

    def test_get_logs_empty_and_not_found(self, sa_session):
        c = _company(sa_session)
        repo = PendingCompanyRepository(sa_session)
        assert repo.get_logs(c.id) == []
        assert repo.get_logs("00000000-0000-0000-0000-000000000000") == []

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