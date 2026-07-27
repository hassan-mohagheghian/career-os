"""Tests for GenerationHistoryRepository.

TDD: Tests written BEFORE implementation.
Tests cover: unified history reads from all 5 source tables.
"""

import sys
import os
import sqlite3
import pytest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.process.generation_models import GenerationHistoryItem
from services.process.generation_repository import GenerationHistoryRepository


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
CREATE TABLE IF NOT EXISTS skill_roadmap_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    job_type TEXT NOT NULL DEFAULT 'generate',
    status TEXT NOT NULL DEFAULT 'queued',
    step INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 4,
    message TEXT DEFAULT '',
    version INTEGER,
    count INTEGER,
    error TEXT,
    session_id TEXT,
    pid INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS career_insight_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_type TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata TEXT DEFAULT '{}',
    session_id TEXT
);
"""


@pytest.fixture
def test_db():
    fd, path = sqlite3.connect(':memory:'), None
    import tempfile
    fd2, path = tempfile.mkstemp(suffix='.db')
    os.close(fd2)
    conn = sqlite3.connect(path)
    conn.executescript(ALL_TABLES)
    conn.commit()
    conn.close()
    yield path
    os.remove(path)


@pytest.fixture
def repo(test_db):
    return GenerationHistoryRepository(test_db)


class TestGenerationHistoryRepository:
    """Test unified generation history reads from all source tables."""

    def test_empty_db_returns_empty(self, repo):
        result = repo.get_all()
        assert result['items'] == []
        assert result['total'] == 0

    def test_reads_pending_jobs(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO pending_jobs (url, company, status, session_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ('https://example.com/job1', 'Acme', 'done', 'sess_1', '2026-07-27T10:00:00', '2026-07-27T10:05:00'),
        )
        conn.commit()
        conn.close()

        result = repo.get_all()
        assert result['total'] == 1
        item = result['items'][0]
        assert item.source == 'job-processing'
        assert item.title == 'Acme'
        assert item.status == 'done'
        assert item.session_id == 'sess_1'

    def test_reads_pending_companies(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO pending_companies (input_text, company_name, status, session_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ('https://example.com/co1', 'TechCorp', 'done', 'sess_co', '2026-07-27T10:00:00', '2026-07-27T10:03:00'),
        )
        conn.commit()
        conn.close()

        result = repo.get_all()
        assert result['total'] == 1
        item = result['items'][0]
        assert item.source == 'company-processing'
        assert item.title == 'TechCorp'

    def test_reads_pending_generations(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO pending_generations (job_num, type, status, session_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (1, 'resume', 'done', 'sess_gen', '2026-07-27T10:00:00', '2026-07-27T10:02:00'),
        )
        conn.commit()
        conn.close()

        result = repo.get_all()
        assert result['total'] == 1
        item = result['items'][0]
        assert item.source == 'generation'
        assert item.title == 'Resume'

    def test_reads_skill_roadmap_jobs(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO skill_roadmap_jobs (skill_name, job_type, status, session_id, started_at, completed_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ('Python', 'generate', 'completed', 'sess_rm', '2026-07-27T10:00:00', '2026-07-27T10:04:00'),
        )
        conn.commit()
        conn.close()

        result = repo.get_all()
        assert result['total'] == 1
        item = result['items'][0]
        assert item.source == 'roadmap'
        assert 'Python' in item.title
        assert 'generate' in item.title

    def test_reads_career_insight_runs(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO career_insight_runs (insight_type, status, session_id, started_at, completed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ('overview', 'completed', 'sess_ci', '2026-07-27T10:00:00', '2026-07-27T10:06:00'),
        )
        conn.commit()
        conn.close()

        result = repo.get_all()
        assert result['total'] == 1
        item = result['items'][0]
        assert item.source == 'insights'
        assert item.title == 'Overview'

    def test_unified_sorting(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        # Insert items from different sources with different timestamps
        conn.execute(
            "INSERT INTO pending_jobs (url, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ('url1', 'done', '2026-07-27T09:00:00', '2026-07-27T09:05:00'),
        )
        conn.execute(
            "INSERT INTO career_insight_runs (insight_type, status, started_at, completed_at) VALUES (?, ?, ?, ?)",
            ('market', 'completed', '2026-07-27T10:00:00', '2026-07-27T10:03:00'),
        )
        conn.execute(
            "INSERT INTO skill_roadmap_jobs (skill_name, job_type, status, started_at, completed_at) VALUES (?, ?, ?, ?, ?)",
            ('React', 'extend', 'completed', '2026-07-27T11:00:00', '2026-07-27T11:02:00'),
        )
        conn.commit()
        conn.close()

        result = repo.get_all()
        assert result['total'] == 3
        # Should be sorted by most recent first
        assert result['items'][0].source == 'roadmap'  # 11:00
        assert result['items'][1].source == 'insights'  # 10:00
        assert result['items'][2].source == 'job-processing'  # 09:00

    def test_pagination(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        for i in range(5):
            conn.execute(
                "INSERT INTO career_insight_runs (insight_type, status, started_at) VALUES (?, ?, ?)",
                (f'type_{i}', 'completed', f'2026-07-27T10:0{i}:00'),
            )
        conn.commit()
        conn.close()

        page1 = repo.get_all(limit=2, offset=0)
        assert len(page1['items']) == 2
        assert page1['total'] == 5

        page2 = repo.get_all(limit=2, offset=2)
        assert len(page2['items']) == 2
        assert page2['total'] == 5

        page3 = repo.get_all(limit=2, offset=4)
        assert len(page3['items']) == 1

    def test_filter_by_source(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO pending_jobs (url, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ('url1', 'done', '2026-07-27T10:00:00', '2026-07-27T10:01:00'),
        )
        conn.execute(
            "INSERT INTO career_insight_runs (insight_type, status, started_at) VALUES (?, ?, ?)",
            ('overview', 'completed', '2026-07-27T10:00:00'),
        )
        conn.commit()
        conn.close()

        result = repo.get_all(source_filter='job-processing')
        assert result['total'] == 1
        assert result['items'][0].source == 'job-processing'

    def test_error_captured(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO pending_jobs (url, status, error, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            ('url1', 'failed', 'Connection timeout', '2026-07-27T10:00:00', '2026-07-27T10:01:00'),
        )
        conn.commit()
        conn.close()

        result = repo.get_all()
        assert result['items'][0].error == 'Connection timeout'
