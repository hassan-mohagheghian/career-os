"""Tests for JobQueueManager — graceful shutdown, cancel, reset, transitions."""

import os
import sqlite3
import tempfile
import threading
import time

import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE IF NOT EXISTS pending_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE, source TEXT DEFAULT 'cli',
        status TEXT DEFAULT 'queued', version INTEGER DEFAULT 1,
        queue_order INTEGER DEFAULT 0,
        step_fetch INTEGER DEFAULT 0, step_validate INTEGER DEFAULT 0,
        step_extract_raw INTEGER DEFAULT 0, step_extract_struct INTEGER DEFAULT 0,
        step_analyze INTEGER DEFAULT 0, step_summary INTEGER DEFAULT 0,
        step_db INTEGER DEFAULT 0, step_done INTEGER DEFAULT 0,
        job_num INTEGER, company TEXT, error TEXT,
        workflow_log TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS pending_companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        input_text TEXT NOT NULL, notes TEXT DEFAULT '[]',
        input_type TEXT DEFAULT 'url', source TEXT DEFAULT 'web',
        status TEXT DEFAULT 'pending', version INTEGER DEFAULT 1,
        step_fetch INTEGER DEFAULT 0, step_extract INTEGER DEFAULT 0,
        step_analyze INTEGER DEFAULT 0, step_save INTEGER DEFAULT 0,
        step_done INTEGER DEFAULT 0,
        company_id INTEGER, company_name TEXT, error TEXT,
        links TEXT DEFAULT '[]',
        workflow_log TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()
    yield path
    os.remove(path)


@pytest.fixture
def queue(db_path):
    import core.queue as q
    q.DB_PATH = db_path
    mgr = q.JobQueueManager(concurrency=2)
    yield mgr
    mgr._running = False


def _insert_job(conn, url, status='pending'):
    cur = conn.execute(
        "INSERT INTO pending_jobs (url, status) VALUES (?, ?)", (url, status)
    )
    conn.commit()
    return cur.lastrowid


def _insert_company(conn, text, status='pending'):
    cur = conn.execute(
        "INSERT INTO pending_companies (input_text, status) VALUES (?, ?)", (text, status)
    )
    conn.commit()
    return cur.lastrowid


class TestTransitionValidation:
    def test_valid_transitions(self):
        from core.queue import VALID_TRANSITIONS
        assert 'queued' in VALID_TRANSITIONS['pending']
        assert 'processing' in VALID_TRANSITIONS['queued']
        assert 'done' in VALID_TRANSITIONS['processing']
        assert 'failed' in VALID_TRANSITIONS['processing']
        assert 'paused' in VALID_TRANSITIONS['processing']

    def test_invalid_transition(self):
        from core.queue import VALID_TRANSITIONS
        assert 'done' not in VALID_TRANSITIONS['pending']
        assert 'processing' not in VALID_TRANSITIONS['pending']


class TestEnqueue:
    def test_enqueue_job(self, queue, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_job(conn, 'https://example.com', 'pending')
        conn.close()

        queue.enqueue(pid)
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT status, queue_order FROM pending_jobs WHERE id=?", (pid,)).fetchone()
        conn.close()
        assert row[0] == 'queued'
        assert row[1] > 0

    def test_enqueue_company(self, queue, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_company(conn, 'TestCorp', 'pending')
        conn.close()

        queue.enqueue(pid, table='pending_companies')
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT status FROM pending_companies WHERE id=?", (pid,)).fetchone()
        conn.close()
        assert row[0] == 'queued'

    def test_enqueue_bulk(self, queue, db_path):
        conn = sqlite3.connect(db_path)
        ids = [_insert_job(conn, f'https://example{i}.com') for i in range(5)]
        conn.close()

        queue.enqueue_bulk(ids)
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT status, queue_order FROM pending_jobs WHERE id IN ({})".format(
            ','.join('?' * len(ids))
        ), ids).fetchall()
        conn.close()
        assert all(r[0] == 'queued' for r in rows)
        orders = [r[1] for r in rows]
        assert orders == sorted(orders)  # FIFO order preserved


class TestCancelJob:
    def test_cancel_queued(self, queue, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_job(conn, 'https://example.com', 'queued')
        conn.close()

        ok = queue.cancel_job(pid)
        assert ok
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT status FROM pending_jobs WHERE id=?", (pid,)).fetchone()
        conn.close()
        assert row[0] == 'pending'

    def test_cancel_nonexistent(self, queue):
        assert not queue.cancel_job(999)

    def test_cancel_processing_without_process(self, queue, db_path):
        """Cancel a 'processing' job when no subprocess exists — should set paused."""
        conn = sqlite3.connect(db_path)
        pid = _insert_job(conn, 'https://example.com', 'processing')
        conn.close()

        ok = queue.cancel_job(pid)
        assert ok
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT status FROM pending_jobs WHERE id=?", (pid,)).fetchone()
        conn.close()
        assert row[0] == 'paused'


class TestResetJob:
    def test_reset_processing(self, queue, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_job(conn, 'https://example.com', 'processing')
        conn.execute("UPDATE pending_jobs SET step_fetch=1, step_analyze=1 WHERE id=?", (pid,))
        conn.commit()
        conn.close()

        ok = queue.reset_job(pid)
        assert ok
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT status, step_fetch, step_analyze, step_done FROM pending_jobs WHERE id=?", (pid,)
        ).fetchone()
        conn.close()
        assert row[0] == 'pending'
        assert row[1] == 0  # step_fetch reset
        assert row[2] == 0  # step_analyze reset
        assert row[3] == 0  # step_done reset

    def test_reset_company(self, queue, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_company(conn, 'TestCorp', 'processing')
        conn.execute("UPDATE pending_companies SET step_fetch=1 WHERE id=?", (pid,))
        conn.commit()
        conn.close()

        ok = queue.reset_job(pid, table='pending_companies')
        assert ok
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT status, step_fetch FROM pending_companies WHERE id=?", (pid,)
        ).fetchone()
        conn.close()
        assert row[0] == 'pending'
        assert row[1] == 0

    def test_reset_nonexistent(self, queue):
        assert not queue.reset_job(999)


class TestDequeue:
    def test_dequeue(self, queue, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_job(conn, 'https://example.com', 'queued')
        conn.close()

        queue.dequeue(pid)
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT status, queue_order FROM pending_jobs WHERE id=?", (pid,)).fetchone()
        conn.close()
        assert row[0] == 'pending'
        assert row[1] == 0


class TestGetStatus:
    def test_empty_queue(self, queue):
        status = queue.get_status()
        assert status['processing_count'] == 0
        assert status['queued_count'] == 0
        assert status['pending_count'] == 0
        assert status['concurrency'] == 2
        assert status['running'] is False

    def test_with_items(self, queue, db_path):
        conn = sqlite3.connect(db_path)
        _insert_job(conn, 'https://a.com', 'pending')
        _insert_job(conn, 'https://b.com', 'queued')
        _insert_job(conn, 'https://c.com', 'processing')
        conn.close()

        status = queue.get_status()
        assert status['pending_count'] == 1
        assert status['queued_count'] == 1
        assert status['processing_count'] == 1


class TestMarkProcessingAsPaused:
    def test_marks_processing_as_paused(self, queue, db_path):
        conn = sqlite3.connect(db_path)
        _insert_job(conn, 'https://a.com', 'processing')
        _insert_job(conn, 'https://b.com', 'processing')
        _insert_job(conn, 'https://c.com', 'queued')
        conn.close()

        queue._mark_processing_as_paused()
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT status FROM pending_jobs ORDER BY id").fetchall()
        conn.close()
        statuses = [r[0] for r in rows]
        assert statuses.count('paused') == 2
        assert statuses.count('queued') == 1


class TestOrphanRecovery:
    def test_reset_orphans(self, queue, db_path):
        conn = sqlite3.connect(db_path)
        _insert_job(conn, 'https://a.com', 'processing')
        _insert_job(conn, 'https://b.com', 'processing')
        conn.close()

        queue._reset_processing_orphans()
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT status FROM pending_jobs").fetchall()
        conn.close()
        assert all(r[0] == 'queued' for r in rows)


class TestGracefulShutdown:
    def test_stop_sets_running_false(self, queue):
        queue._running = True
        queue.stop(timeout=1)
        assert not queue._running
