"""Tests for PendingJobRepository — SQLite persistence layer."""

import os
import sqlite3
import tempfile

import pytest
from services.process.repository import PendingJobRepository, JobRepository
from services.process.models import ItemStatus, WorkflowLogEntry


@pytest.fixture
def db_path():
    """Create a temp DB with the required schema."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE IF NOT EXISTS pending_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE, source TEXT DEFAULT 'cli',
        status TEXT DEFAULT 'queued', queue_order INTEGER DEFAULT 0,
        step_fetch INTEGER DEFAULT 0, step_validate INTEGER DEFAULT 0,
        step_extract_raw INTEGER DEFAULT 0, step_extract_struct INTEGER DEFAULT 0,
        step_analyze INTEGER DEFAULT 0, step_summary INTEGER DEFAULT 0,
        step_db INTEGER DEFAULT 0, step_done INTEGER DEFAULT 0,
        job_num INTEGER, company TEXT, error TEXT,
        workflow_log TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
        num INTEGER PRIMARY KEY, company TEXT, role TEXT, url TEXT,
        match TEXT, score TEXT, success TEXT, salary TEXT, stack TEXT,
        visa TEXT, applicants TEXT, posted TEXT, industry TEXT,
        domain TEXT, notes TEXT, action TEXT, work_type TEXT DEFAULT 'On-site',
        workflow_log TEXT DEFAULT '[]', created_at TIMESTAMP,
        posted_at TEXT, locations TEXT DEFAULT '[]', deleted INTEGER DEFAULT 0,
        employment_type TEXT DEFAULT 'Full-time', work_types TEXT DEFAULT '[]',
        raw_description TEXT, structured_description TEXT,
        raw_file_path TEXT, structured_file_path TEXT,
        rescoring INTEGER DEFAULT 0, adv_at TEXT, see_at TEXT,
        apply_reason TEXT, company_url TEXT, linkedin_url TEXT,
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
def pending_repo(db_path):
    return PendingJobRepository(db_path)


@pytest.fixture
def job_repo(db_path):
    return JobRepository(db_path)


class TestPendingJobRepository:
    def test_insert_and_get(self, pending_repo, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)",
                     ('https://example.com', 'queued'))
        conn.commit()
        conn.close()

        item = pending_repo.get(1)
        assert item is not None
        assert item['url'] == 'https://example.com'
        assert item['status'] == 'queued'

    def test_get_nonexistent(self, pending_repo):
        assert pending_repo.get(999) is None

    def test_update_status(self, pending_repo, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)",
                     ('https://example.com', 'queued'))
        conn.commit()
        conn.close()

        pending_repo.update_status(1, ItemStatus.PROCESSING)
        item = pending_repo.get(1)
        assert item['status'] == 'processing'

    def test_update_step(self, pending_repo, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)",
                     ('https://example.com', 'processing'))
        conn.commit()
        conn.close()

        pending_repo.update_step(1, 'step_fetch', 1)
        item = pending_repo.get(1)
        assert item['step_fetch'] == 1

    def test_append_log(self, pending_repo, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)",
                     ('https://example.com', 'processing'))
        conn.commit()
        conn.close()

        entry = WorkflowLogEntry(step='fetch', msg='Fetched 1000 chars', ts='12:00:00')
        pending_repo.append_log(1, entry)

        logs = pending_repo.get_logs(1)
        assert len(logs) == 1
        assert logs[0].msg == 'Fetched 1000 chars'

    def test_claim_next(self, pending_repo, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO pending_jobs (url, status, queue_order) VALUES (?, ?, ?)",
                     ('https://a.com', 'queued', 1))
        conn.execute("INSERT INTO pending_jobs (url, status, queue_order) VALUES (?, ?, ?)",
                     ('https://b.com', 'queued', 2))
        conn.commit()
        conn.close()

        claimed = pending_repo.claim_next()
        assert claimed is not None
        assert claimed['url'] == 'https://a.com'

        item = pending_repo.get(claimed['id'])
        assert item['status'] == 'processing'

    def test_claim_next_empty(self, pending_repo):
        assert pending_repo.claim_next() is None

    def test_count_by_status(self, pending_repo, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)",
                     ('https://a.com', 'queued'))
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)",
                     ('https://b.com', 'processing'))
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)",
                     ('https://c.com', 'done'))
        conn.commit()
        conn.close()

        counts = pending_repo.count_by_status()
        assert counts[ItemStatus.QUEUED] == 1
        assert counts[ItemStatus.PROCESSING] == 1
        assert counts[ItemStatus.DONE] == 1
        assert counts[ItemStatus.PENDING] == 0


class TestJobRepository:
    def test_get_next_num(self, job_repo, db_path):
        assert job_repo.get_next_num() == 1

        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO jobs (num, company, url) VALUES (?, ?, ?)",
                     (5, 'Corp', 'https://x.com'))
        conn.commit()
        conn.close()

        assert job_repo.get_next_num() == 6

    def test_get_by_url(self, job_repo, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO jobs (num, company, url, score, match, deleted) VALUES (?, ?, ?, ?, ?, ?)",
                     (1, 'Corp', 'https://x.com', 'A', 'High', 0))
        conn.commit()
        conn.close()

        job = job_repo.get_by_url('https://x.com')
        assert job is not None
        assert job['company'] == 'Corp'

    def test_get_by_url_deleted(self, job_repo, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO jobs (num, company, url, score, match, deleted) VALUES (?, ?, ?, ?, ?, ?)",
                     (1, 'Corp', 'https://x.com', 'A', 'High', 1))
        conn.commit()
        conn.close()

        assert job_repo.get_by_url('https://x.com') is None
