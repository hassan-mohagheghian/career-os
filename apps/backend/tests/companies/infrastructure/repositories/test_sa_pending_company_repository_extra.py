"""Extra tests for SQLAlchemyPendingCompanyRepository.

Covers branch combinations for pending_companies (CompanyModel): update_status
company, create with notes, count variants, get_processing_items,
mark_processing_as_waiting / reset_processing_orphans, get_queued_items,
get_all_for_stream, delete paths, direct create, update_step and
update_workflow_log.
"""

import json

import pytest

from companies.infrastructure.models.company_model import CompanyModel
from companies.infrastructure.repositories.sa_pending_company_repository import SQLAlchemyPendingCompanyRepository


@pytest.fixture
def repo(sa_session):
    return SQLAlchemyPendingCompanyRepository(sa_session)


def _company(sa_session, **kwargs):
    defaults = {"name": "Corp"}
    defaults.update(kwargs)
    m = CompanyModel(**defaults)
    sa_session.add(m)
    sa_session.commit()
    sa_session.refresh(m)
    return m


class TestUpdateStatus:
    def test_update_status_company(self, sa_session, repo):
        c = _company(sa_session, status="queued")
        assert repo.update_status(str(c.id), "processing", table="pending_companies") is True
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first()
        assert row.status == "processing"

    def test_update_status_company_not_found(self, repo):
        assert repo.update_status("999", "processing", table="pending_companies") is False


class TestCreate:
    def test_create_company_with_notes(self, sa_session, repo):
        result = repo.create({"notes": [1, 2]}, "pending_companies")
        assert result["status"] == "created"
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == result["id"]).first()
        assert json.loads(row.notes) == [1, 2]


class TestCounts:
    def test_get_pending_count_companies(self, sa_session, repo):
        _company(sa_session, status="pending")
        _company(sa_session, status="created")
        assert repo.get_pending_count("pending_companies") == 1

    def test_get_processing_count_companies(self, sa_session, repo):
        _company(sa_session, status="processing")
        _company(sa_session, status="queued")
        assert repo.get_processing_count("pending_companies") == 1

    def test_get_queued_count_companies(self, sa_session, repo):
        _company(sa_session, status="queued")
        _company(sa_session, status="pending")
        assert repo.get_queued_count("pending_companies") == 1


class TestProcessingHelpers:
    def test_get_processing_items_companies(self, sa_session, repo):
        c = _company(sa_session, status="processing")
        _company(sa_session, status="queued")
        items = repo.get_processing_items("pending_companies")
        assert len(items) == 1
        assert items[0]["id"] == c.id

    def test_mark_processing_as_waiting_companies(self, sa_session, repo):
        _company(sa_session, status="processing")
        count = repo.mark_processing_as_waiting("pending_companies")
        assert count == 1
        row = sa_session.query(CompanyModel).filter(CompanyModel.status == "processing").first()
        assert row is None

    def test_reset_processing_orphans_companies(self, sa_session, repo):
        _company(sa_session, status="processing")
        _company(sa_session, status="queued")
        count = repo.reset_processing_orphans("pending_companies")
        assert count == 1
        row = sa_session.query(CompanyModel).filter(CompanyModel.status == "created").first()
        assert row is not None


class TestQueuedItems:
    def test_get_queued_items_companies(self, sa_session, repo):
        c = _company(sa_session, status="queued")
        _company(sa_session, status="pending")
        items = repo.get_queued_items("pending_companies")
        assert len(items) == 1
        assert items[0]["id"] == c.id


class TestStreamAndDelete:
    def test_get_all_for_stream_companies(self, sa_session, repo):
        c = _company(sa_session, status="pending")
        rows = repo.get_all_for_stream("pending_companies")
        assert len(rows) == 1
        assert rows[0]["id"] == c.id

    def test_delete_company_found(self, sa_session, repo):
        c = _company(sa_session)
        assert repo.delete(c.id, "pending_companies") is True
        assert sa_session.query(CompanyModel).filter(CompanyModel.id == c.id).first() is None

    def test_delete_company_not_found(self, repo):
        assert repo.delete("00000000-0000-0000-0000-000000000000", "pending_companies") is False

    def test_create_pending_company(self, repo):
        result = repo.create_pending_company("SomeCo", "url", "web", "created", "[]")
        assert result["status"] == "created"

    def test_create_pending_company_persists_name(self, sa_session, repo):
        result = repo.create_pending_company("SomeCo", "url", "web", "created", "[]", name="Acme GmbH")
        assert result["name"] == "Acme GmbH"
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == result["id"]).first()
        assert row.input_text == "SomeCo"
        assert row.input_type == "url"

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
