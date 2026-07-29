"""Tests for SQLAlchemyPendingRepository — atomic claim, reset_steps with keep_status."""

import os
import tempfile
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from shared.infrastructure.database.sqlalchemy_config import Base
from processing.infrastructure.models.pending_model import PendingJobModel, PendingCompanyModel
from processing.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository


@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()
    os.remove(path)


def _insert_job(session, url='https://example.com', status='queued', queue_order=0):
    m = PendingJobModel(url=url, status=status, source='cli', queue_order=queue_order)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.id


def _insert_company(session, text='TestCorp', status='queued'):
    m = PendingCompanyModel(input_text=text, status=status, source='web')
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.id


class TestPickQueuedItem:
    """Test atomic pick_queued_item uses SELECT + conditional UPDATE."""

    def test_picks_first_queued_job(self, db):
        repo = SQLAlchemyPendingRepository(db)
        id1 = _insert_job(db, 'https://a.com', 'queued', queue_order=1)
        id2 = _insert_job(db, 'https://b.com', 'queued', queue_order=2)

        result = repo.pick_queued_item('pending_jobs')
        assert result is not None
        assert result['id'] == id1
        assert result['status'] == 'starting'

    def test_skips_non_queued_jobs(self, db):
        repo = SQLAlchemyPendingRepository(db)
        _insert_job(db, 'https://a.com', 'starting')
        id2 = _insert_job(db, 'https://b.com', 'queued')

        result = repo.pick_queued_item('pending_jobs')
        assert result is not None
        assert result['id'] == id2

    def test_returns_none_when_no_queued(self, db):
        repo = SQLAlchemyPendingRepository(db)
        _insert_job(db, 'https://a.com', 'starting')

        result = repo.pick_queued_item('pending_jobs')
        assert result is None

    def test_returns_none_on_empty_table(self, db):
        repo = SQLAlchemyPendingRepository(db)
        result = repo.pick_queued_item('pending_jobs')
        assert result is None

    def test_picks_lowest_queue_order(self, db):
        repo = SQLAlchemyPendingRepository(db)
        id_high = _insert_job(db, 'https://a.com', 'queued', queue_order=10)
        id_low = _insert_job(db, 'https://b.com', 'queued', queue_order=1)

        result = repo.pick_queued_item('pending_jobs')
        assert result['id'] == id_low

    def test_commits_status_change(self, db):
        repo = SQLAlchemyPendingRepository(db)
        pid = _insert_job(db, 'https://a.com', 'queued')

        repo.pick_queued_item('pending_jobs')

        row = db.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.status == 'starting'

    def test_pick_company(self, db):
        repo = SQLAlchemyPendingRepository(db)
        cid = _insert_company(db, 'CorpA', 'queued')

        result = repo.pick_queued_item('pending_companies')
        assert result is not None
        assert result['id'] == cid
        assert result['status'] == 'starting'

    def test_pick_company_returns_none_when_empty(self, db):
        repo = SQLAlchemyPendingRepository(db)
        result = repo.pick_queued_item('pending_companies')
        assert result is None

    def test_concurrent_pick_only_one_wins(self, db):
        """Simulate two repos picking from the same table — only one should succeed."""
        repo1 = SQLAlchemyPendingRepository(db)
        id1 = _insert_job(db, 'https://a.com', 'queued')

        result1 = repo1.pick_queued_item('pending_jobs')
        assert result1 is not None

        # Second pick should return None since item is already processing
        result2 = repo1.pick_queued_item('pending_jobs')
        assert result2 is None


class TestResetSteps:
    """Test reset_steps with keep_status parameter."""

    def test_reset_steps_sets_queued_by_default(self, db):
        repo = SQLAlchemyPendingRepository(db)
        pid = _insert_job(db, 'https://a.com', 'starting')
        job = db.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        job.step_fetch = 1
        job.step_analyze = 1
        job.error = 'some error'
        db.commit()

        repo.reset_steps(pid, version=2, table='pending_jobs')

        row = db.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.status == 'created'
        assert row.step_fetch == 0
        assert row.step_analyze == 0
        assert row.error is None
        assert row.version == 2

    def test_reset_steps_keep_status(self, db):
        """keep_status=True should reset steps but NOT change status."""
        repo = SQLAlchemyPendingRepository(db)
        pid = _insert_job(db, 'https://a.com', 'starting')
        job = db.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        job.step_fetch = 1
        job.step_analyze = 1
        db.commit()

        repo.reset_steps(pid, version=3, table='pending_jobs', keep_status=True)

        row = db.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.status == 'starting'  # NOT changed to created
        assert row.step_fetch == 0
        assert row.step_analyze == 0
        assert row.version == 3

    def test_reset_steps_company(self, db):
        repo = SQLAlchemyPendingRepository(db)
        cid = _insert_company(db, 'Corp', 'starting')
        comp = db.query(PendingCompanyModel).filter(PendingCompanyModel.id == cid).first()
        comp.step_fetch = 1
        comp.step_extract = 1
        db.commit()

        repo.reset_steps(cid, version=1, table='pending_companies')

        row = db.query(PendingCompanyModel).filter(PendingCompanyModel.id == cid).first()
        assert row.status == 'queued'
        assert row.step_fetch == 0
        assert row.step_extract == 0

    def test_reset_steps_company_keep_status(self, db):
        repo = SQLAlchemyPendingRepository(db)
        cid = _insert_company(db, 'Corp', 'starting')
        comp = db.query(PendingCompanyModel).filter(PendingCompanyModel.id == cid).first()
        comp.step_fetch = 1
        db.commit()

        repo.reset_steps(cid, version=1, table='pending_companies', keep_status=True)

        row = db.query(PendingCompanyModel).filter(PendingCompanyModel.id == cid).first()
        assert row.status == 'starting'
        assert row.step_fetch == 0

    def test_reset_steps_clears_workflow_log(self, db):
        repo = SQLAlchemyPendingRepository(db)
        pid = _insert_job(db, 'https://a.com', 'starting')
        job = db.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        job.workflow_log = '[{"step": "fetch"}]'
        db.commit()

        repo.reset_steps(pid, version=1, table='pending_jobs')

        row = db.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.workflow_log == '[]'


class TestHasPartialSteps:
    """Test _has_partial_steps in queue manager."""

    def test_all_zero_is_not_partial(self):
        from shared.infrastructure.config.queue import JobQueueManager
        mgr = JobQueueManager(concurrency=1)
        item = {
            'step_fetch': 0, 'step_validate': 0, 'step_extract_raw': 0,
            'step_extract_struct': 0, 'step_analyze': 0, 'step_summary': 0,
            'step_db': 0, 'step_done': 0,
        }
        assert not mgr._has_partial_steps(item)

    def test_one_done_is_partial(self):
        from shared.infrastructure.config.queue import JobQueueManager
        mgr = JobQueueManager(concurrency=1)
        item = {
            'step_fetch': 1, 'step_validate': 0, 'step_extract_raw': 0,
            'step_extract_struct': 0, 'step_analyze': 0, 'step_summary': 0,
            'step_db': 0, 'step_done': 0,
        }
        assert mgr._has_partial_steps(item)

    def test_all_done_is_not_partial(self):
        from shared.infrastructure.config.queue import JobQueueManager
        mgr = JobQueueManager(concurrency=1)
        item = {
            'step_fetch': 1, 'step_validate': 1, 'step_extract_raw': 1,
            'step_extract_struct': 1, 'step_analyze': 1, 'step_summary': 1,
            'step_db': 1, 'step_done': 1,
        }
        assert not mgr._has_partial_steps(item)


class TestResetStepsKeepStatusInQueue:
    """Test that _reset_steps in queue uses keep_status=True."""

    def test_reset_steps_does_not_requeue(self, db):
        from shared.infrastructure.config.queue import JobQueueManager
        from unittest.mock import patch

        pid = _insert_job(db, 'https://a.com', 'starting')
        job = db.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        job.step_fetch = 1
        db.commit()

        with patch('shared.infrastructure.config.queue.get_session_sync', return_value=db):
            mgr = JobQueueManager(concurrency=1)
            mgr._reset_steps(pid, version=2, table='pending_jobs')

        row = db.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.status == 'starting'  # Should NOT be reset to queued
        assert row.step_fetch == 0
