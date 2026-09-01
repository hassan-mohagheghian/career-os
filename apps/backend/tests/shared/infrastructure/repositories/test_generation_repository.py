"""Tests for GenerationHistoryRepository.

TDD: Tests written BEFORE implementation.
Tests cover: unified history reads from all source tables.
"""

import sys
import os
import pytest
from datetime import datetime
from unittest.mock import patch
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.infrastructure.database.sqlalchemy_config import Base
from jobs.infrastructure.models.job_model import JobModel
from companies.infrastructure.models.company_model import CompanyModel

from shared.domain.models.generation_models import GenerationHistoryItem
from shared.infrastructure.repositories.generation_repository import GenerationHistoryRepository


@pytest.fixture
def sa_session(_engine):
    connection = _engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def repo(sa_session):
    with patch('shared.infrastructure.repositories.generation_repository.get_session_sync', return_value=sa_session):
        yield GenerationHistoryRepository()


class TestGenerationHistoryRepository:
    """Test unified generation history reads from all source tables."""

    def test_empty_db_returns_empty(self, repo):
        result = repo.get_all()
        assert result['items'] == []
        assert result['total'] == 0

    def test_reads_pending_jobs(self, repo, sa_session):
        m = JobModel(
            url='https://example.com/job1',
            source='web', company='Acme', status='done',
            workflow_log='[]', queue_order=0,
            session_id='sess_1',
            created_at='2026-07-27T10:00:00',
            updated_at='2026-07-27T10:05:00',
            user_id="test-user",
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
        m = CompanyModel(
            name='TechCorp', source='web', status='done',
            workflow_log='[]',
            created_at='2026-07-27T10:00:00',
            updated_at='2026-07-27T10:03:00',
            user_id="test-user",
        )
        sa_session.add(m)
        sa_session.commit()

        result = repo.get_all()
        assert result['total'] == 1
        item = result['items'][0]
        assert item.source == 'company-processing'
        assert item.title == 'TechCorp'

    def test_reads_pending_generations(self, repo, sa_session):
        """pending_generations table has been removed - this test is a no-op."""
        pass

    def test_error_captured(self, repo, sa_session):
        m = JobModel(
            url='url1', source='web', status='failed',
            error='Connection timeout',
            workflow_log='[]', queue_order=0,
            created_at='2026-07-27T10:00:00',
            updated_at='2026-07-27T10:01:00',
            user_id="test-user",
        )
        sa_session.add(m)
        sa_session.commit()

        result = repo.get_all()
        assert result['items'][0].error == 'Connection timeout'
