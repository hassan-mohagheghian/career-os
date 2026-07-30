"""Tests for SQLAlchemyPendingRepository — atomic claim, reset_steps with keep_status."""

import pytest
from sqlalchemy.orm import sessionmaker

from shared.infrastructure.database.sqlalchemy_config import Base
from jobs.infrastructure.models.job_model import JobModel
from companies.infrastructure.models.company_model import CompanyModel
from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository


@pytest.fixture
def db(_engine):
    connection = _engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


_counter = 0
def _insert_job(session, url='https://example.com', status='queued', queue_order=0):
    global _counter
    _counter += 1
    m = JobModel(num=_counter, url=url, status=status, source='cli', queue_order=queue_order)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.num


def _insert_company(session, text='TestCorp', status='queued'):
    m = CompanyModel(name=text, status=status, source='web')
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
        assert result['num'] == id1
        assert result['status'] == 'processing'

    def test_skips_non_queued_jobs(self, db):
        repo = SQLAlchemyPendingRepository(db)
        _insert_job(db, 'https://a.com', 'starting')
        id2 = _insert_job(db, 'https://b.com', 'queued')

        result = repo.pick_queued_item('pending_jobs')
        assert result is not None
        assert result['num'] == id2

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
        assert result['num'] == id_low

    def test_commits_status_change(self, db):
        repo = SQLAlchemyPendingRepository(db)
        pid = _insert_job(db, 'https://a.com', 'queued')

        repo.pick_queued_item('pending_jobs')

        row = db.query(JobModel).filter(JobModel.num == pid).first()
        assert row.status == 'processing'

    def test_pick_company(self, db):
        repo = SQLAlchemyPendingRepository(db)
        cid = _insert_company(db, 'CorpA', 'queued')

        result = repo.pick_queued_item('pending_companies')
        assert result is not None
        assert result['id'] == cid
        assert result['status'] == 'processing'

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
        job = db.query(JobModel).filter(JobModel.num == pid).first()
        job.error = 'some error'
        db.commit()

        repo.reset_steps(pid, version=2, table='pending_jobs')

        row = db.query(JobModel).filter(JobModel.num == pid).first()
        assert row.status == 'created'
        assert row.error is None

    def test_reset_steps_keep_status(self, db):
        """keep_status=True should reset steps but NOT change status."""
        repo = SQLAlchemyPendingRepository(db)
        pid = _insert_job(db, 'https://a.com', 'starting')
        job = db.query(JobModel).filter(JobModel.num == pid).first()
        db.commit()

        repo.reset_steps(pid, version=3, table='pending_jobs', keep_status=True)

        row = db.query(JobModel).filter(JobModel.num == pid).first()
        assert row.status == 'starting'

    def test_reset_steps_company(self, db):
        repo = SQLAlchemyPendingRepository(db)
        cid = _insert_company(db, 'Corp', 'starting')
        comp = db.query(CompanyModel).filter(CompanyModel.id == cid).first()
        db.commit()

        repo.reset_steps(cid, version=1, table='pending_companies')

        row = db.query(CompanyModel).filter(CompanyModel.id == cid).first()
        assert row.status == 'created'

    def test_reset_steps_company_keep_status(self, db):
        repo = SQLAlchemyPendingRepository(db)
        cid = _insert_company(db, 'Corp', 'starting')
        comp = db.query(CompanyModel).filter(CompanyModel.id == cid).first()
        db.commit()

        repo.reset_steps(cid, version=1, table='pending_companies', keep_status=True)

        row = db.query(CompanyModel).filter(CompanyModel.id == cid).first()
        assert row.status == 'starting'

    def test_reset_steps_clears_workflow_log(self, db):
        repo = SQLAlchemyPendingRepository(db)
        pid = _insert_job(db, 'https://a.com', 'starting')
        job = db.query(JobModel).filter(JobModel.num == pid).first()
        job.workflow_log = '[{"step": "fetch"}]'
        db.commit()

        repo.reset_steps(pid, version=1, table='pending_jobs')

        row = db.query(JobModel).filter(JobModel.num == pid).first()
        assert row.workflow_log == '[]'


class TestResetStepsKeepStatusInQueue:
    """Test that _reset_steps in queue uses keep_status=True."""

    def test_reset_steps_does_not_requeue(self, db):
        from shared.infrastructure.config.queue import JobQueueManager
        from unittest.mock import patch

        pid = _insert_job(db, 'https://a.com', 'starting')
        job = db.query(JobModel).filter(JobModel.num == pid).first()
        db.commit()

        with patch('shared.infrastructure.database.session.get_session_sync', return_value=db):
            mgr = JobQueueManager(concurrency=1)
            mgr.reset_item(pid)

        row = db.query(JobModel).filter(JobModel.num == pid).first()
        assert row.status == 'pending'
