"""Tests for GenerationHistoryRepository.

TDD: Tests written BEFORE implementation.
Tests cover: unified history reads from all 5 source tables.
"""

import sys
import os
import sqlite3
import pytest
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.sqlalchemy_config import Base
import infrastructure.database.models.pending_model
import infrastructure.database.models.insight_model
import infrastructure.database.models.misc_models

from services.process.generation_models import GenerationHistoryItem
from services.process.generation_repository import GenerationHistoryRepository


@pytest.fixture
def test_db():
    import tempfile
    fd2, path = tempfile.mkstemp(suffix='.db')
    os.close(fd2)
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()
    yield path
    os.remove(path)


@pytest.fixture
def repo(test_db):
    engine = create_engine(f"sqlite:///{test_db}")
    Session = sessionmaker(bind=engine)
    sa_session = Session()
    with patch('services.process.generation_repository.get_session_sync', return_value=sa_session):
        yield GenerationHistoryRepository()
    sa_session.close()
    engine.dispose()


class TestGenerationHistoryRepository:
    """Test unified generation history reads from all source tables."""

    def test_empty_db_returns_empty(self, repo):
        result = repo.get_all()
        assert result['items'] == []
        assert result['total'] == 0

    def test_reads_pending_jobs(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO pending_jobs "
            "(url, source, company, status, version, notes, links, "
            "step_fetch, step_analyze, step_resume, step_cover, step_db, step_done, "
            "workflow_log, queue_order, step_extract_raw, step_extract_struct, "
            "session_id, created_at, updated_at) "
            "VALUES (?, 'web', ?, 'done', 1, '[]', '[]', "
            "0, 0, 0, 0, 0, 0, "
            "'[]', 0, 0, 0, "
            "?, ?, ?)",
            ('https://example.com/job1', 'Acme', 'sess_1', '2026-07-27T10:00:00', '2026-07-27T10:05:00'),
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
            "INSERT INTO pending_companies "
            "(input_text, source, company_name, status, version, notes, links, input_type, "
            "step_fetch, step_extract, step_analyze, step_save, step_done, "
            "workflow_log, created_at, updated_at) "
            "VALUES (?, 'web', ?, 'done', 1, '[]', '[]', 'url', "
            "0, 0, 0, 0, 0, "
            "'[]', ?, ?)",
            ('https://example.com/co1', 'TechCorp', '2026-07-27T10:00:00', '2026-07-27T10:03:00'),
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
            "INSERT INTO pending_generations "
            "(job_num, type, status, step_prepare, step_context, step_generate, step_save, step_done, "
            "session_id, created_at, updated_at) "
            "VALUES (1, 'resume', 'queued', 0, 0, 0, 0, 0, "
            "?, ?, ?)",
            ('sess_gen', '2026-07-27T10:00:00', '2026-07-27T10:02:00'),
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
            "INSERT INTO skill_roadmap_jobs "
            "(skill_name, job_type, status, step, total_steps, message, "
            "session_id, started_at, completed_at) "
            "VALUES ('Python', 'generate', 'completed', 0, 4, '', "
            "?, ?, ?)",
            ('sess_rm', '2026-07-27T10:00:00', '2026-07-27T10:04:00'),
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
            "INSERT INTO career_insight_runs "
            "(insight_type, version, status, metadata, session_id, started_at, completed_at) "
            "VALUES ('overview', 1, 'completed', '{}', ?, ?, ?)",
            ('sess_ci', '2026-07-27T10:00:00', '2026-07-27T10:06:00'),
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
        conn.execute(
            "INSERT INTO pending_jobs "
            "(url, source, status, version, notes, links, "
            "step_fetch, step_analyze, step_resume, step_cover, step_db, step_done, "
            "workflow_log, queue_order, step_extract_raw, step_extract_struct, "
            "created_at, updated_at) "
            "VALUES ('url1', 'web', 'done', 1, '[]', '[]', "
            "0, 0, 0, 0, 0, 0, "
            "'[]', 0, 0, 0, "
            "?, ?)",
            ('2026-07-27T09:00:00', '2026-07-27T09:05:00'),
        )
        conn.execute(
            "INSERT INTO career_insight_runs "
            "(insight_type, version, status, metadata, started_at, completed_at) "
            "VALUES ('market', 1, 'completed', '{}', ?, ?)",
            ('2026-07-27T10:00:00', '2026-07-27T10:03:00'),
        )
        conn.execute(
            "INSERT INTO skill_roadmap_jobs "
            "(skill_name, job_type, status, step, total_steps, message, "
            "started_at, completed_at) "
            "VALUES ('React', 'extend', 'completed', 0, 4, '', "
            "?, ?)",
            ('2026-07-27T11:00:00', '2026-07-27T11:02:00'),
        )
        conn.commit()
        conn.close()

        result = repo.get_all()
        assert result['total'] == 3
        assert result['items'][0].source == 'roadmap'
        assert result['items'][1].source == 'insights'
        assert result['items'][2].source == 'job-processing'

    def test_pagination(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        for i in range(5):
            conn.execute(
                "INSERT INTO career_insight_runs "
                "(insight_type, version, status, metadata, started_at) "
                "VALUES (?, 1, 'completed', '{}', ?)",
                (f'type_{i}', f'2026-07-27T10:0{i}:00'),
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
            "INSERT INTO pending_jobs "
            "(url, source, status, version, notes, links, "
            "step_fetch, step_analyze, step_resume, step_cover, step_db, step_done, "
            "workflow_log, queue_order, step_extract_raw, step_extract_struct, "
            "created_at, updated_at) "
            "VALUES ('url1', 'web', 'done', 1, '[]', '[]', "
            "0, 0, 0, 0, 0, 0, "
            "'[]', 0, 0, 0, "
            "?, ?)",
            ('2026-07-27T10:00:00', '2026-07-27T10:01:00'),
        )
        conn.execute(
            "INSERT INTO career_insight_runs "
            "(insight_type, version, status, metadata, started_at) "
            "VALUES ('overview', 1, 'completed', '{}', ?)",
            ('2026-07-27T10:00:00',),
        )
        conn.commit()
        conn.close()

        result = repo.get_all(source_filter='job-processing')
        assert result['total'] == 1
        assert result['items'][0].source == 'job-processing'

    def test_error_captured(self, repo, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO pending_jobs "
            "(url, source, status, error, version, notes, links, "
            "step_fetch, step_analyze, step_resume, step_cover, step_db, step_done, "
            "workflow_log, queue_order, step_extract_raw, step_extract_struct, "
            "created_at, updated_at) "
            "VALUES ('url1', 'web', 'failed', 'Connection timeout', 1, '[]', '[]', "
            "0, 0, 0, 0, 0, 0, "
            "'[]', 0, 0, 0, "
            "?, ?)",
            ('2026-07-27T10:00:00', '2026-07-27T10:01:00'),
        )
        conn.commit()
        conn.close()

        result = repo.get_all()
        assert result['items'][0].error == 'Connection timeout'
