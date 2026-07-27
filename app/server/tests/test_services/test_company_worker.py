"""Tests for company_worker.py utility functions."""

import os
import tempfile
import sqlite3
import json
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.sqlalchemy_config import Base
import infrastructure.database.models.pending_model
import infrastructure.database.models.company_model
from infrastructure.database.models.pending_model import PendingCompanyModel


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
    """Insert a pending_companies row via SA ORM."""
    m = PendingCompanyModel(input_text=input_text, status=status)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.id


# ── DB Helpers ─────────────────────────────────────────────────────

class TestCompanyDbHelpers:
    pass


# ── Update Step ────────────────────────────────────────────────────

class TestCompanyUpdateStep:
    def test_update_step(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'processing')

        from services.company_worker import _update_step
        with patch('services.company_worker.get_session_sync', return_value=sa_session):
            _update_step(pid, 'step_fetch', 1)

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT step_fetch FROM pending_companies WHERE id=?", (pid,)).fetchone()
        conn.close()
        assert row[0] == 1

    def test_update_step_with_status(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'queued')

        from services.company_worker import _update_step
        with patch('services.company_worker.get_session_sync', return_value=sa_session):
            _update_step(pid, 'step_fetch', 0, status='processing')

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT step_fetch, status FROM pending_companies WHERE id=?", (pid,)).fetchone()
        conn.close()
        assert row[0] == 0
        assert row[1] == 'processing'


# ── Log ────────────────────────────────────────────────────────────

class TestCompanyLog:
    def test_append_log(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'processing')

        from services.company_worker import _log
        with patch('services.company_worker.get_session_sync', return_value=sa_session):
            _log(pid, 'fetch', 'Fetching URL...')

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT workflow_log FROM pending_companies WHERE id=?", (pid,)).fetchone()
        conn.close()
        logs = json.loads(row[0])
        assert len(logs) == 1
        assert logs[0]['step'] == 'fetch'
        assert logs[0]['msg'] == 'Fetching URL...'


# ── Is Paused Or Stopped ──────────────────────────────────────────

class TestCompanyIsPausedOrStopped:
    def test_item_deleted(self, db_path):
        sa_session = _make_session(db_path)
        from services.company_worker import _is_paused_or_stopped
        with patch('services.company_worker.get_session_sync', return_value=sa_session):
            assert _is_paused_or_stopped(999) is True

    def test_processing(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'processing')

        from services.company_worker import _is_paused_or_stopped
        with patch('services.company_worker.get_session_sync', return_value=sa_session):
            assert _is_paused_or_stopped(pid) is False

    def test_paused(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'paused')

        from services.company_worker import _is_paused_or_stopped
        with patch('services.company_worker.get_session_sync', return_value=sa_session):
            assert _is_paused_or_stopped(pid) is True


# ── Fail ───────────────────────────────────────────────────────────

class TestCompanyFail:
    def test_fail_sets_status(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'processing')

        from services.company_worker import _fail
        with patch('services.company_worker.get_session_sync', return_value=sa_session):
            _fail(pid, 'Something went wrong', step='fetch')

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT status, error FROM pending_companies WHERE id=?", (pid,)).fetchone()
        conn.close()
        assert row[0] == 'failed'
        assert '[Fetching content] Something went wrong' in row[1]

    def test_fail_without_step(self, db_path):
        sa_session = _make_session(db_path)
        pid = _insert_company(sa_session, 'TestCorp', 'processing')

        from services.company_worker import _fail
        with patch('services.company_worker.get_session_sync', return_value=sa_session):
            _fail(pid, 'Generic error')

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT error FROM pending_companies WHERE id=?", (pid,)).fetchone()
        conn.close()
        assert row[0] == 'Generic error'
