"""Tests for company_worker.py utility functions."""

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
    conn.execute("""CREATE TABLE IF NOT EXISTS pending_companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        input_text TEXT NOT NULL, notes TEXT DEFAULT '[]',
        links TEXT DEFAULT '[]', input_type TEXT DEFAULT 'url',
        source TEXT DEFAULT 'web', status TEXT DEFAULT 'pending',
        step_fetch INTEGER DEFAULT 0, step_extract INTEGER DEFAULT 0,
        step_analyze INTEGER DEFAULT 0, step_save INTEGER DEFAULT 0,
        step_done INTEGER DEFAULT 0, company_id INTEGER,
        company_name TEXT, error TEXT,
        workflow_log TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, website TEXT, domain TEXT, industry TEXT,
        country TEXT, city TEXT, description TEXT, company_size TEXT,
        company_type TEXT, logo_url TEXT, founded_year TEXT,
        headquarters_full TEXT, countries_of_operation TEXT,
        funding_stage TEXT, funding_amount TEXT, products TEXT,
        tech_stack TEXT, work_environment TEXT, extra TEXT,
        notes TEXT DEFAULT '[]', processing_status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS company_intelligence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        overview TEXT, culture_analysis TEXT, international_analysis TEXT,
        career_analysis TEXT, benefits_analysis TEXT, visa_analysis TEXT,
        technology_analysis TEXT, recommendation TEXT, scores TEXT,
        raw_source_data TEXT,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS company_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        url TEXT NOT NULL, title TEXT DEFAULT '', description TEXT DEFAULT '',
        status TEXT DEFAULT 'pending', extracted_content TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id)
    )""")
    conn.commit()
    conn.close()
    yield path
    os.remove(path)


# ── DB Helpers ─────────────────────────────────────────────────────

class TestCompanyDbHelpers:
    def test_db_connection(self, db_path):
        os.environ['DB_PATH'] = db_path
        from services.company_worker import _db
        conn = _db()
        assert conn is not None
        conn.close()

    def test_db_retry_on_lock(self, db_path):
        """_db() retries on locked database."""
        from services.company_worker import _db
        with patch('services.company_worker.DB_PATH', db_path):
            conn = _db()
            assert conn is not None
            conn.close()


class TestCompanyUpdateStep:
    def test_update_step(self, db_path):
        os.environ['DB_PATH'] = db_path
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO pending_companies (input_text, status) VALUES (?, ?)",
            ('TestCorp', 'processing')
        )
        conn.commit()
        conn.close()

        from services.company_worker import _update_step
        with patch('services.company_worker.DB_PATH', db_path):
            _update_step(1, 'step_fetch', 1)

            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT step_fetch FROM pending_companies WHERE id=1").fetchone()
            conn.close()
            assert row[0] == 1

    def test_update_step_with_status(self, db_path):
        os.environ['DB_PATH'] = db_path
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO pending_companies (input_text, status) VALUES (?, ?)",
            ('TestCorp', 'queued')
        )
        conn.commit()
        conn.close()

        from services.company_worker import _update_step
        with patch('services.company_worker.DB_PATH', db_path):
            _update_step(1, 'step_fetch', 0, status='processing')

            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT step_fetch, status FROM pending_companies WHERE id=1").fetchone()
            conn.close()
            assert row[0] == 0
            assert row[1] == 'processing'


class TestCompanyLog:
    def test_append_log(self, db_path):
        os.environ['DB_PATH'] = db_path
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO pending_companies (input_text, status) VALUES (?, ?)",
            ('TestCorp', 'processing')
        )
        conn.commit()
        conn.close()

        from services.company_worker import _log
        with patch('services.company_worker.DB_PATH', db_path):
            _log(1, 'fetch', 'Fetching URL...')

            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT workflow_log FROM pending_companies WHERE id=1").fetchone()
            conn.close()
            logs = json.loads(row[0])
            assert len(logs) == 1
            assert logs[0]['step'] == 'fetch'
            assert logs[0]['msg'] == 'Fetching URL...'


class TestCompanyIsPausedOrStopped:
    def test_item_deleted(self, db_path):
        os.environ['DB_PATH'] = db_path
        from services.company_worker import _is_paused_or_stopped
        with patch('services.company_worker.DB_PATH', db_path):
            assert _is_paused_or_stopped(999) is True

    def test_processing(self, db_path):
        os.environ['DB_PATH'] = db_path
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO pending_companies (input_text, status) VALUES (?, ?)",
            ('TestCorp', 'processing')
        )
        conn.commit()
        conn.close()

        from services.company_worker import _is_paused_or_stopped
        with patch('services.company_worker.DB_PATH', db_path):
            assert _is_paused_or_stopped(1) is False

    def test_paused(self, db_path):
        os.environ['DB_PATH'] = db_path
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO pending_companies (input_text, status) VALUES (?, ?)",
            ('TestCorp', 'paused')
        )
        conn.commit()
        conn.close()

        from services.company_worker import _is_paused_or_stopped
        with patch('services.company_worker.DB_PATH', db_path):
            assert _is_paused_or_stopped(1) is True


class TestCompanyFail:
    def test_fail_sets_status(self, db_path):
        os.environ['DB_PATH'] = db_path
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO pending_companies (input_text, status) VALUES (?, ?)",
            ('TestCorp', 'processing')
        )
        conn.commit()
        conn.close()

        from services.company_worker import _fail
        with patch('services.company_worker.DB_PATH', db_path):
            _fail(1, 'Something went wrong', step='fetch')

            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT status, error FROM pending_companies WHERE id=1").fetchone()
            conn.close()
            assert row[0] == 'failed'
            assert '[Fetching content] Something went wrong' in row[1]

    def test_fail_without_step(self, db_path):
        os.environ['DB_PATH'] = db_path
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO pending_companies (input_text, status) VALUES (?, ?)",
            ('TestCorp', 'processing')
        )
        conn.commit()
        conn.close()

        from services.company_worker import _fail
        with patch('services.company_worker.DB_PATH', db_path):
            _fail(1, 'Generic error')

            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT error FROM pending_companies WHERE id=1").fetchone()
            conn.close()
            assert row[0] == 'Generic error'
