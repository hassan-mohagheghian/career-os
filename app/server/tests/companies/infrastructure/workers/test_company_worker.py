"""Tests for company_worker.py utility functions."""

import os
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.infrastructure.database.sqlalchemy_config import Base
from companies.infrastructure.models.company_model import CompanyModel


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    yield path
    os.remove(path)


def _make_session(db_path):
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    return Session()


def _insert_company(session, input_text='TestCorp', status='processing'):
    """Insert a companies row via SA ORM."""
    m = CompanyModel(name=input_text, status=status)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.id


# ── Update Step ────────────────────────────────────────────────────

class TestCompanyUpdateStep:
    def test_update_step(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'processing')

        from companies.infrastructure.workers.company_worker import _update_step
        with patch('companies.infrastructure.workers.company_worker.get_session_sync', return_value=sa_session):
            _update_step(pid, 'step_fetch', 1)

        row = sa_session.query(CompanyModel).filter(CompanyModel.id == pid).first()
        assert row.updated_at is not None

    def test_update_step_with_status(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'queued')

        from companies.infrastructure.workers.company_worker import _update_step
        with patch('companies.infrastructure.workers.company_worker.get_session_sync', return_value=sa_session):
            _update_step(pid, 'step_fetch', 0, status='processing')

        row = sa_session.query(CompanyModel).filter(CompanyModel.id == pid).first()
        assert row.status == 'processing'


# ── Log ────────────────────────────────────────────────────────────

class TestCompanyLog:
    def test_append_log(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'processing')

        from companies.infrastructure.workers.company_worker import _log
        with patch('companies.infrastructure.workers.company_worker.get_session_sync', return_value=sa_session):
            _log(pid, 'fetch', 'Fetching URL...')

        row = sa_session.query(CompanyModel).filter(CompanyModel.id == pid).first()
        logs = json.loads(row.workflow_log)
        assert len(logs) == 1
        assert logs[0]['step'] == 'fetch'
        assert logs[0]['msg'] == 'Fetching URL...'


# ── Is Paused Or Stopped ──────────────────────────────────────────

class TestCompanyIsPausedOrStopped:
    def test_item_deleted(self, db_path):
        sa_session = _make_session(db_path)
        from companies.infrastructure.workers.company_worker import _is_paused_or_stopped
        with patch('companies.infrastructure.workers.company_worker.get_session_sync', return_value=sa_session):
            assert _is_paused_or_stopped(999) is True

    def test_processing(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'processing')

        from companies.infrastructure.workers.company_worker import _is_paused_or_stopped
        with patch('companies.infrastructure.workers.company_worker.get_session_sync', return_value=sa_session):
            assert _is_paused_or_stopped(pid) is False

    def test_paused(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'paused')

        from companies.infrastructure.workers.company_worker import _is_paused_or_stopped
        with patch('companies.infrastructure.workers.company_worker.get_session_sync', return_value=sa_session):
            assert _is_paused_or_stopped(pid) is True


# ── Fail ───────────────────────────────────────────────────────────

class TestCompanyFail:
    def test_fail_sets_status(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'processing')

        from companies.infrastructure.workers.company_worker import _fail
        with patch('companies.infrastructure.workers.company_worker.get_session_sync', return_value=sa_session):
            _fail(pid, 'Something went wrong', step='fetch')

        row = sa_session.query(CompanyModel).filter(CompanyModel.id == pid).first()
        assert row.status == 'failed'

    def test_fail_without_step(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'processing')

        from companies.infrastructure.workers.company_worker import _fail
        with patch('companies.infrastructure.workers.company_worker.get_session_sync', return_value=sa_session):
            _fail(pid, 'Generic error')

        row = sa_session.query(CompanyModel).filter(CompanyModel.id == pid).first()
        assert row.error == 'Generic error'
