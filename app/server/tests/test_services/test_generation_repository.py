"""Tests for GenerationHistoryRepository.

TDD: Tests written BEFORE implementation.
Tests cover: unified history reads from all 5 source tables.
"""

import sys
import os
import tempfile
import pytest
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.sqlalchemy_config import Base
from infrastructure.database.models.pending_model import PendingJobModel, PendingCompanyModel, PendingGenerationModel
from infrastructure.database.models.misc_models import SkillRoadmapJobModel
from infrastructure.database.models.insight_model import CareerInsightRunModel

from services.process.generation_models import GenerationHistoryItem
from services.process.generation_repository import GenerationHistoryRepository


@pytest.fixture
def test_db():
    fd2, path = tempfile.mkstemp(suffix='.db')
    os.close(fd2)
    yield path
    os.remove(path)


@pytest.fixture
def sa_session(test_db):
    engine = create_engine(f"sqlite:///{test_db}")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def repo(sa_session):
    with patch('services.process.generation_repository.get_session_sync', return_value=sa_session):
        yield GenerationHistoryRepository()


class TestGenerationHistoryRepository:
    """Test unified generation history reads from all source tables."""

    def test_empty_db_returns_empty(self, repo):
        result = repo.get_all()
        assert result['items'] == []
        assert result['total'] == 0

    def test_reads_pending_jobs(self, repo, sa_session):
        m = PendingJobModel(
            url='https://example.com/job1',
            source='web',
            company='Acme',
            status='done',
            version=1,
            notes='[]',
            links='[]',
            step_fetch=0,
            step_analyze=0,
            step_resume=0,
            step_cover=0,
            step_db=0,
            step_done=0,
            workflow_log='[]',
            queue_order=0,
            step_extract_raw=0,
            step_extract_struct=0,
            session_id='sess_1',
            created_at='2026-07-27T10:00:00',
            updated_at='2026-07-27T10:05:00',
        )
        sa_session.add(m)
        sa_session.commit()

        result = repo.get_all()
        assert result['total'] == 1
        item = result['items'][0]
        assert item.source == 'job-processing'
        assert item.title == 'Acme'
        assert item.status == 'done'
        assert item.session_id == 'sess_1'

    def test_reads_pending_companies(self, repo, sa_session):
        m = PendingCompanyModel(
            input_text='https://example.com/co1',
            source='web',
            company_name='TechCorp',
            status='done',
            version=1,
            notes='[]',
            links='[]',
            input_type='url',
            step_fetch=0,
            step_extract=0,
            step_analyze=0,
            step_save=0,
            step_done=0,
            workflow_log='[]',
            created_at='2026-07-27T10:00:00',
            updated_at='2026-07-27T10:03:00',
        )
        sa_session.add(m)
        sa_session.commit()

        result = repo.get_all()
        assert result['total'] == 1
        item = result['items'][0]
        assert item.source == 'company-processing'
        assert item.title == 'TechCorp'

    def test_reads_pending_generations(self, repo, sa_session):
        m = PendingGenerationModel(
            job_num=1,
            type='resume',
            status='queued',
            step_prepare=0,
            step_context=0,
            step_generate=0,
            step_save=0,
            step_done=0,
            session_id='sess_gen',
            created_at='2026-07-27T10:00:00',
            updated_at='2026-07-27T10:02:00',
        )
        sa_session.add(m)
        sa_session.commit()

        result = repo.get_all()
        assert result['total'] == 1
        item = result['items'][0]
        assert item.source == 'generation'
        assert item.title == 'Resume'

    def test_reads_skill_roadmap_jobs(self, repo, sa_session):
        m = SkillRoadmapJobModel(
            skill_name='Python',
            job_type='generate',
            status='completed',
            step=0,
            total_steps=4,
            message='',
            session_id='sess_rm',
            started_at='2026-07-27T10:00:00',
            completed_at='2026-07-27T10:04:00',
        )
        sa_session.add(m)
        sa_session.commit()

        result = repo.get_all()
        assert result['total'] == 1
        item = result['items'][0]
        assert item.source == 'roadmap'
        assert 'Python' in item.title
        assert 'generate' in item.title

    def test_reads_career_insight_runs(self, repo, sa_session):
        m = CareerInsightRunModel(
            insight_type='overview',
            version=1,
            status='completed',
            metadata_json='{}',
            session_id='sess_ci',
            started_at='2026-07-27T10:00:00',
            completed_at='2026-07-27T10:06:00',
        )
        sa_session.add(m)
        sa_session.commit()

        result = repo.get_all()
        assert result['total'] == 1
        item = result['items'][0]
        assert item.source == 'insights'
        assert item.title == 'Overview'

    def test_unified_sorting(self, repo, sa_session):
        job = PendingJobModel(
            url='url1',
            source='web',
            status='done',
            version=1,
            notes='[]',
            links='[]',
            step_fetch=0,
            step_analyze=0,
            step_resume=0,
            step_cover=0,
            step_db=0,
            step_done=0,
            workflow_log='[]',
            queue_order=0,
            step_extract_raw=0,
            step_extract_struct=0,
            created_at='2026-07-27T09:00:00',
            updated_at='2026-07-27T09:05:00',
        )
        insight = CareerInsightRunModel(
            insight_type='market',
            version=1,
            status='completed',
            metadata_json='{}',
            started_at='2026-07-27T10:00:00',
            completed_at='2026-07-27T10:03:00',
        )
        roadmap = SkillRoadmapJobModel(
            skill_name='React',
            job_type='extend',
            status='completed',
            step=0,
            total_steps=4,
            message='',
            started_at='2026-07-27T11:00:00',
            completed_at='2026-07-27T11:02:00',
        )
        sa_session.add_all([job, insight, roadmap])
        sa_session.commit()

        result = repo.get_all()
        assert result['total'] == 3
        assert result['items'][0].source == 'roadmap'
        assert result['items'][1].source == 'insights'
        assert result['items'][2].source == 'job-processing'

    def test_pagination(self, repo, sa_session):
        for i in range(5):
            m = CareerInsightRunModel(
                insight_type=f'type_{i}',
                version=1,
                status='completed',
                metadata_json='{}',
                started_at=f'2026-07-27T10:0{i}:00',
            )
            sa_session.add(m)
        sa_session.commit()

        page1 = repo.get_all(limit=2, offset=0)
        assert len(page1['items']) == 2
        assert page1['total'] == 5

        page2 = repo.get_all(limit=2, offset=2)
        assert len(page2['items']) == 2
        assert page2['total'] == 5

        page3 = repo.get_all(limit=2, offset=4)
        assert len(page3['items']) == 1

    def test_filter_by_source(self, repo, sa_session):
        job = PendingJobModel(
            url='url1',
            source='web',
            status='done',
            version=1,
            notes='[]',
            links='[]',
            step_fetch=0,
            step_analyze=0,
            step_resume=0,
            step_cover=0,
            step_db=0,
            step_done=0,
            workflow_log='[]',
            queue_order=0,
            step_extract_raw=0,
            step_extract_struct=0,
            created_at='2026-07-27T10:00:00',
            updated_at='2026-07-27T10:01:00',
        )
        insight = CareerInsightRunModel(
            insight_type='overview',
            version=1,
            status='completed',
            metadata_json='{}',
            started_at='2026-07-27T10:00:00',
        )
        sa_session.add_all([job, insight])
        sa_session.commit()

        result = repo.get_all(source_filter='job-processing')
        assert result['total'] == 1
        assert result['items'][0].source == 'job-processing'

    def test_error_captured(self, repo, sa_session):
        m = PendingJobModel(
            url='url1',
            source='web',
            status='failed',
            error='Connection timeout',
            version=1,
            notes='[]',
            links='[]',
            step_fetch=0,
            step_analyze=0,
            step_resume=0,
            step_cover=0,
            step_db=0,
            step_done=0,
            workflow_log='[]',
            queue_order=0,
            step_extract_raw=0,
            step_extract_struct=0,
            created_at='2026-07-27T10:00:00',
            updated_at='2026-07-27T10:01:00',
        )
        sa_session.add(m)
        sa_session.commit()

        result = repo.get_all()
        assert result['items'][0].error == 'Connection timeout'
