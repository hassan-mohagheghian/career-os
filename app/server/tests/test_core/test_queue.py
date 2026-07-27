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
    yield path
    os.remove(path)


@pytest.fixture
def queue(db_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from infrastructure.database.sqlalchemy_config import Base
    import infrastructure.database.models.pending_model

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    sa_session = Session()

    import core.queue as q
    with patch('core.queue.get_session_sync', return_value=sa_session):
        mgr = q.JobQueueManager(concurrency=2)
        yield mgr
    mgr._running = False
    sa_session.close()
    engine.dispose()


def _insert_job(conn, url, status='pending'):
    cur = conn.execute(
        """INSERT INTO pending_jobs
           (url, status, source, version, notes, links, workflow_log,
            step_fetch, step_analyze, step_resume, step_cover, step_db, step_done,
            queue_order, step_extract_raw, step_extract_struct)
           VALUES (?, ?, 'cli', 1, '[]', '[]', '[]',
                   0, 0, 0, 0, 0, 0,
                   0, 0, 0)""",
        (url, status),
    )
    conn.commit()
    return cur.lastrowid


def _insert_company(conn, text, status='pending'):
    cur = conn.execute(
        """INSERT INTO pending_companies
           (input_text, status, notes, input_type, source, version,
            step_fetch, step_extract, step_analyze, step_save, step_done,
            workflow_log, links)
           VALUES (?, ?, '[]', 'url', 'web', 1,
                   0, 0, 0, 0, 0,
                   '[]', '[]')""",
        (text, status),
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
        assert row[0] == 'queued'
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
        assert row[0] == 'queued'
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
