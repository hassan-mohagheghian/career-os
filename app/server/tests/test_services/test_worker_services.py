"""Tests for worker services (JobWorker, CompanyWorker, GenerationWorker).

TDD: Tests written BEFORE implementation.
Tests cover: WorkerBase subclassing, pipeline execution, status transitions.
"""

import sys
import os
import sqlite3
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.process.generation_models import GenerationSource, GenerationStatus
from services.process.models import ItemStatus, WorkflowLogEntry, StatusUpdate, ProcessingComplete
from services.process.worker_base import WorkerBase


ALL_TABLES = """
CREATE TABLE IF NOT EXISTS pending_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL, title TEXT, company TEXT, source TEXT DEFAULT 'web',
    status TEXT DEFAULT 'pending', version INTEGER DEFAULT 1,
    notes TEXT DEFAULT '[]', links TEXT DEFAULT '[]',
    job_num INTEGER,
    step_fetch INTEGER DEFAULT 0, step_validate INTEGER DEFAULT 0,
    step_extract_raw INTEGER DEFAULT 0, step_extract_struct INTEGER DEFAULT 0,
    step_summary INTEGER DEFAULT 0, step_analyze INTEGER DEFAULT 0,
    step_db INTEGER DEFAULT 0, step_done INTEGER DEFAULT 0,
    workflow_log TEXT DEFAULT '[]', error TEXT,
    queue_order INTEGER DEFAULT 0, session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pending_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_text TEXT NOT NULL, notes TEXT DEFAULT '[]',
    links TEXT DEFAULT '[]', input_type TEXT DEFAULT 'url',
    source TEXT DEFAULT 'web', status TEXT DEFAULT 'pending', version INTEGER DEFAULT 1,
    step_fetch INTEGER DEFAULT 0, step_extract INTEGER DEFAULT 0,
    step_analyze INTEGER DEFAULT 0, step_save INTEGER DEFAULT 0,
    step_done INTEGER DEFAULT 0, company_id INTEGER,
    company_name TEXT, error TEXT,
    workflow_log TEXT DEFAULT '[]', session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pending_generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_num INTEGER NOT NULL,
    type TEXT NOT NULL,
    status TEXT DEFAULT 'queued',
    step_prepare INTEGER DEFAULT 0,
    step_context INTEGER DEFAULT 0,
    step_generate INTEGER DEFAULT 0,
    step_save INTEGER DEFAULT 0,
    step_done INTEGER DEFAULT 0,
    result TEXT,
    error TEXT,
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


@pytest.fixture
def test_db():
    fd2, path = tempfile.mkstemp(suffix='.db')
    os.close(fd2)
    conn = sqlite3.connect(path)
    conn.executescript(ALL_TABLES)
    conn.commit()
    conn.close()
    yield path
    os.remove(path)


# ── Concrete WorkerBase implementations for testing ──────────────

class ConcreteWorker(WorkerBase):
    """Test implementation of WorkerBase."""

    @property
    def table(self):
        return 'pending_jobs'

    @property
    def pipeline_steps(self):
        return ['step_fetch', 'step_validate', 'step_done']

    def _execute_pipeline(self, pid, item):
        self._mark_step(pid, 'step_fetch')
        self._log(pid, 'fetch', 'Fetched content')
        if self._is_cancelled(pid):
            return None
        self._mark_step(pid, 'step_validate')
        self._log(pid, 'validate', 'Validated')
        return {'result': 'ok', 'num': 42}


class FailingWorker(WorkerBase):
    """Worker that fails at step 2."""

    @property
    def table(self):
        return 'pending_jobs'

    @property
    def pipeline_steps(self):
        return ['step_fetch', 'step_validate', 'step_done']

    def _execute_pipeline(self, pid, item):
        self._mark_step(pid, 'step_fetch')
        raise RuntimeError("AI service unavailable")


class CompanyTestWorker(WorkerBase):
    """Test company worker."""

    @property
    def table(self):
        return 'pending_companies'

    @property
    def pipeline_steps(self):
        return ['step_fetch', 'step_extract', 'step_analyze', 'step_save', 'step_done']

    def _execute_pipeline(self, pid, item):
        self._mark_step(pid, 'step_fetch')
        self._mark_step(pid, 'step_extract')
        self._mark_step(pid, 'step_analyze')
        self._mark_step(pid, 'step_save')
        return {'company_id': 1, 'name': 'TestCo'}


# ── Tests ──────────────────────────────────────────────────────────

class TestWorkerBase:
    """Test the abstract WorkerBase Template Method pattern."""

    def _make_worker(self, test_db):
        from services.process.repository import PendingJobRepository

        repo = PendingJobRepository(test_db)
        proc_mgr = MagicMock()
        temp_mgr = MagicMock()
        mimo = MagicMock()
        broadcaster = MagicMock()

        return ConcreteWorker(repo, proc_mgr, temp_mgr, mimo, broadcaster)

    def _insert_pending_job(self, test_db, url='https://example.com', status='processing'):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO pending_jobs (url, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (url, status, datetime.now().isoformat(), datetime.now().isoformat()),
        )
        conn.commit()
        pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return pid

    def test_successful_pipeline(self, test_db):
        worker = self._make_worker(test_db)
        pid = self._insert_pending_job(test_db)

        worker.process(pid)

        # Verify final state
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (pid,)).fetchone()
        conn.close()

        assert dict(row)['status'] == 'done'
        assert dict(row)['step_fetch'] == 1
        assert dict(row)['step_validate'] == 1
        assert dict(row)['step_done'] == 1

    def test_failed_pipeline(self, test_db):
        from services.process.repository import PendingJobRepository

        repo = PendingJobRepository(test_db)
        worker = FailingWorker(repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())
        pid = self._insert_pending_job(test_db)

        worker.process(pid)

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (pid,)).fetchone()
        conn.close()

        assert dict(row)['status'] == 'failed'
        assert dict(row)['error'] is not None

    def test_workflow_log_recorded(self, test_db):
        worker = self._make_worker(test_db)
        pid = self._insert_pending_job(test_db)

        worker.process(pid)

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT workflow_log FROM pending_jobs WHERE id=?', (pid,)).fetchone()
        conn.close()

        logs = json.loads(dict(row)['workflow_log'] or '[]')
        assert len(logs) >= 2
        assert logs[0]['msg'] == 'Fetched content'
        assert logs[1]['msg'] == 'Validated'

    def test_missing_item_returns_early(self, test_db):
        worker = self._make_worker(test_db)
        # Process non-existent item - should not raise
        worker.process(99999)

    def test_cancelled_item_stops(self, test_db):
        from services.process.repository import PendingJobRepository

        repo = PendingJobRepository(test_db)
        worker = FailingWorker(repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())
        pid = self._insert_pending_job(test_db, status='paused')

        # Paused item should be detected as cancelled
        assert worker._is_cancelled(pid) is True

    def test_company_worker_table(self, test_db):
        from services.process.repository import PendingCompanyRepository

        repo = PendingCompanyRepository(test_db)
        worker = CompanyTestWorker(repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())

        assert worker.table == 'pending_companies'
        assert len(worker.pipeline_steps) == 5

    def test_reset_steps(self, test_db):
        worker = self._make_worker(test_db)
        pid = self._insert_pending_job(test_db)

        # Manually set steps
        conn = sqlite3.connect(test_db)
        conn.execute("UPDATE pending_jobs SET step_fetch=1, step_validate=1 WHERE id=?", (pid,))
        conn.commit()
        conn.close()

        worker._reset_steps(pid)

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT step_fetch, step_validate FROM pending_jobs WHERE id=?', (pid,)).fetchone()
        conn.close()

        assert dict(row)['step_fetch'] == 0
        assert dict(row)['step_validate'] == 0

    def test_mark_step_broadcasts(self, test_db):
        worker = self._make_worker(test_db)
        pid = self._insert_pending_job(test_db)

        with patch.object(worker._broadcaster, 'step_update') as mock_broadcast:
            worker._mark_step(pid, 'step_fetch', 1)
            mock_broadcast.assert_called_once()
            event = mock_broadcast.call_args[0][0]
            assert isinstance(event, StatusUpdate)
            assert event.step == 'step_fetch'
            assert event.val == 1

    def test_log_appends_entry(self, test_db):
        worker = self._make_worker(test_db)
        pid = self._insert_pending_job(test_db)

        worker._log(pid, 'test', 'Test message')

        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT workflow_log FROM pending_jobs WHERE id=?', (pid,)).fetchone()
        conn.close()

        logs = json.loads(dict(row)['workflow_log'] or '[]')
        assert len(logs) == 1
        assert logs[0]['step'] == 'test'
        assert logs[0]['msg'] == 'Test message'
