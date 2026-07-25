"""Tests for Flask blueprint endpoints — pending, companies, queue status."""

import os
import tempfile
import sqlite3
import json
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
        notes TEXT DEFAULT '[]', links TEXT DEFAULT '[]',
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
        links TEXT DEFAULT '[]', input_type TEXT DEFAULT 'url',
        source TEXT DEFAULT 'web', status TEXT DEFAULT 'pending', version INTEGER DEFAULT 1,
        step_fetch INTEGER DEFAULT 0, step_extract INTEGER DEFAULT 0,
        step_analyze INTEGER DEFAULT 0, step_save INTEGER DEFAULT 0,
        step_done INTEGER DEFAULT 0, company_id INTEGER,
        company_name TEXT, error TEXT,
        workflow_log TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
        num INTEGER PRIMARY KEY, company TEXT, role TEXT, url TEXT,
        match TEXT, score TEXT, salary TEXT, stack TEXT,
        visa TEXT, applicants TEXT, posted TEXT, industry TEXT,
        domain TEXT, notes TEXT, action TEXT, work_type TEXT DEFAULT 'On-site',
        workflow_log TEXT DEFAULT '[]', created_at TIMESTAMP,
        posted_at TEXT, locations TEXT DEFAULT '[]', deleted INTEGER DEFAULT 0,
        employment_type TEXT DEFAULT 'Full-time', work_types TEXT DEFAULT '[]',
        raw_description TEXT, structured_description TEXT,
        raw_file_path TEXT, structured_file_path TEXT,
        rescoring INTEGER DEFAULT 0, success TEXT,
        adv_at TEXT, see_at TEXT, apply_reason TEXT,
        company_url TEXT, linkedin_url TEXT,
        apply_time TEXT, response_time TEXT, response_status TEXT,
        fit_score INTEGER, success_score INTEGER, overall_score INTEGER,
        company_id INTEGER
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS summaries (
        num INTEGER PRIMARY KEY, company TEXT, match TEXT, score TEXT,
        summary TEXT, stack TEXT, resumeFit TEXT, note TEXT, url TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS resumes (
        id TEXT PRIMARY KEY, title TEXT, company TEXT, role TEXT,
        content TEXT, version INTEGER DEFAULT 1, raw_text TEXT,
        created_at TIMESTAMP, job_num INTEGER
    )""")
    conn.commit()
    conn.close()
    yield path
    os.remove(path)


@pytest.fixture
def app(db_path):
    """Create Flask test app with blueprints."""
    os.environ['DB_PATH'] = db_path
    # Patch DB_PATH in all modules that use it
    import core.queue as q
    q.DB_PATH = db_path
    q._queue_manager = None  # reset singleton
    import database as db_mod
    db_mod.DB_PATH = db_path

    from flask import Flask
    from flask_cors import CORS
    app = Flask(__name__)
    CORS(app)
    app.config['TESTING'] = True

    from core.queue import JobQueueManager
    q.DB_PATH = db_path
    q._queue_manager = JobQueueManager(concurrency=2)
    # Don't start workers — tests don't need background processing

    from blueprints.pending import bp as pending_bp
    app.register_blueprint(pending_bp)

    yield app

    # Cleanup
    try:
        if q._queue_manager is not None:
            q._queue_manager.stop(timeout=2)
    except Exception:
        pass
    q._queue_manager = None


@pytest.fixture
def client(app):
    return app.test_client()


def _insert_pending(conn, url, status='pending'):
    cur = conn.execute(
        "INSERT INTO pending_jobs (url, status) VALUES (?, ?)", (url, status)
    )
    conn.commit()
    return cur.lastrowid


# ── GET /api/pending ───────────────────────────────────────────────

class TestGetPending:
    def test_empty_list(self, client):
        resp = client.get('/api/pending')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data == []

    def test_returns_pending_items(self, client, db_path):
        conn = sqlite3.connect(db_path)
        _insert_pending(conn, 'https://example.com')
        _insert_pending(conn, 'https://test.com')
        conn.close()

        resp = client.get('/api/pending')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data) == 2


# ── POST /api/pending ──────────────────────────────────────────────

class TestAddPending:
    def test_add_url(self, client):
        resp = client.post('/api/pending', json={'url': 'https://example.com/job'})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'pending'
        assert data['url'] == 'https://example.com/job'
        assert 'id' in data

    def test_missing_url(self, client):
        resp = client.post('/api/pending', json={})
        assert resp.status_code == 400

    def test_empty_url(self, client):
        resp = client.post('/api/pending', json={'url': ''})
        assert resp.status_code == 400

    def test_duplicate_in_queue(self, client, db_path):
        conn = sqlite3.connect(db_path)
        _insert_pending(conn, 'https://example.com', 'queued')
        conn.close()

        resp = client.post('/api/pending', json={'url': 'https://example.com'})
        assert resp.status_code == 409
        data = json.loads(resp.data)
        assert 'Already in queue' in data['error']

    def test_existing_job_returns_exists(self, client, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO jobs (num, company, url, score, match, deleted) VALUES (?, ?, ?, ?, ?, ?)",
            (1, 'Corp', 'https://example.com', 'A', 'High', 0)
        )
        conn.commit()
        conn.close()

        resp = client.post('/api/pending', json={'url': 'https://example.com'})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'exists'
        assert data['num'] == 1

    def test_source_default(self, client):
        resp = client.post('/api/pending', json={'url': 'https://example.com'})
        data = json.loads(resp.data)
        assert data['source'] == 'web'

    def test_source_custom(self, client):
        resp = client.post('/api/pending', json={'url': 'https://example.com', 'source': 'cli'})
        data = json.loads(resp.data)
        assert data['source'] == 'cli'


# ── DELETE /api/pending/<id> ───────────────────────────────────────

class TestDeletePending:
    def test_delete_existing(self, client, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_pending(conn, 'https://example.com')
        conn.close()

        resp = client.delete(f'/api/pending/{pid}')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'deleted'

        # Verify deleted
        resp = client.get('/api/pending')
        data = json.loads(resp.data)
        assert len(data) == 0

    def test_delete_cascades_job(self, client, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_pending(conn, 'https://example.com')
        conn.execute(
            "INSERT INTO jobs (num, company, url, score, match, deleted) VALUES (?, ?, ?, ?, ?, ?)",
            (1, 'Corp', 'https://example.com', 'A', 'High', 0)
        )
        conn.commit()
        conn.close()

        resp = client.delete(f'/api/pending/{pid}')
        assert resp.status_code == 200

        # Verify job marked deleted
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT deleted FROM jobs WHERE num=1").fetchone()
        conn.close()
        assert row[0] == 1


# ── PUT /api/pending/<id>/reset ────────────────────────────────────

class TestResetPending:
    def test_reset_queued(self, client, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_pending(conn, 'https://example.com', 'queued')
        conn.close()

        resp = client.put(f'/api/pending/{pid}/reset')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'pending'

    def test_reset_nonexistent(self, client):
        resp = client.put('/api/pending/999/reset')
        assert resp.status_code == 404


# ── PUT /api/pending/<id>/cancel ───────────────────────────────────

class TestCancelPending:
    def test_cancel_queued(self, client, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_pending(conn, 'https://example.com', 'queued')
        conn.close()

        resp = client.put(f'/api/pending/{pid}/cancel')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'paused'

    def test_cancel_nonexistent(self, client):
        resp = client.put('/api/pending/999/cancel')
        assert resp.status_code == 404


# ── PUT /api/pending/<id>/pause ────────────────────────────────────

class TestPausePending:
    def test_pause_queued(self, client, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_pending(conn, 'https://example.com', 'queued')
        conn.close()

        resp = client.put(f'/api/pending/{pid}/pause')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'paused'


# ── POST /api/pending/<id>/process ─────────────────────────────────

class TestProcessPending:
    def test_process_pending_item(self, client, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_pending(conn, 'https://example.com', 'pending')
        conn.close()

        resp = client.post(f'/api/pending/{pid}/process')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'queued'

    def test_process_already_done(self, client, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_pending(conn, 'https://example.com', 'done')
        conn.close()

        resp = client.post(f'/api/pending/{pid}/process')
        assert resp.status_code == 400

    def test_process_already_processing(self, client, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_pending(conn, 'https://example.com', 'processing')
        conn.close()

        resp = client.post(f'/api/pending/{pid}/process')
        assert resp.status_code == 409

    def test_process_failed_resets(self, client, db_path):
        conn = sqlite3.connect(db_path)
        pid = _insert_pending(conn, 'https://example.com', 'failed')
        conn.execute("UPDATE pending_jobs SET error='old error', step_fetch=1 WHERE id=?", (pid,))
        conn.commit()
        conn.close()

        resp = client.post(f'/api/pending/{pid}/process')
        assert resp.status_code == 200

        # Verify steps reset
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT step_fetch, error FROM pending_jobs WHERE id=?", (pid,)).fetchone()
        conn.close()
        assert row[0] == 0  # step_fetch reset
        assert row[1] is None  # error cleared


# ── POST /api/pending/queue-all ────────────────────────────────────

class TestQueueAll:
    def test_queue_all_pending(self, client, db_path):
        conn = sqlite3.connect(db_path)
        _insert_pending(conn, 'https://a.com', 'pending')
        _insert_pending(conn, 'https://b.com', 'pending')
        _insert_pending(conn, 'https://c.com', 'queued')  # already queued
        conn.close()

        resp = client.post('/api/pending/queue-all')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['count'] == 2

    def test_queue_all_empty(self, client):
        resp = client.post('/api/pending/queue-all')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['count'] == 0


# ── GET /api/queue/status ──────────────────────────────────────────

class TestQueueStatus:
    def test_empty_queue(self, client):
        resp = client.get('/api/queue/status')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['processing_count'] == 0
        assert data['queued_count'] == 0
        assert data['pending_count'] == 0
        assert data['concurrency'] == 2

    def test_with_items(self, client, db_path):
        conn = sqlite3.connect(db_path)
        _insert_pending(conn, 'https://a.com', 'pending')
        _insert_pending(conn, 'https://b.com', 'queued')
        _insert_pending(conn, 'https://c.com', 'processing')
        conn.close()

        resp = client.get('/api/queue/status')
        data = json.loads(resp.data)
        assert data['pending_count'] == 1
        assert data['queued_count'] == 1
        assert data['processing_count'] == 1
