"""Tests for JobQueueManager — graceful shutdown, cancel, reset, transitions."""

import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from processing.infrastructure.models.pending_model import PendingCompanyModel, PendingJobModel
from shared.infrastructure.database.sqlalchemy_config import Base


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix='.db')
    import os
    os.close(fd)
    yield path
    os.remove(path)


@pytest.fixture
def queue(db_path):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    sa_session = Session()

    import shared.infrastructure.config.queue as q
    from unittest.mock import patch
    with patch('shared.infrastructure.config.queue.get_session_sync', return_value=sa_session):
        mgr = q.JobQueueManager(concurrency=2)
        yield mgr, sa_session
    mgr._running = False
    sa_session.close()
    engine.dispose()


def _insert_job(session, url, status='pending'):
    m = PendingJobModel(url=url, status=status, source='cli')
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.id


def _insert_company(session, text, status='pending'):
    m = PendingCompanyModel(input_text=text, status=status, source='web')
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.id


class TestTransitionValidation:
    def test_valid_transitions(self):
        from shared.infrastructure.config.queue import VALID_TRANSITIONS
        assert 'queued' in VALID_TRANSITIONS['pending']
        assert 'processing' in VALID_TRANSITIONS['queued']
        assert 'done' in VALID_TRANSITIONS['processing']
        assert 'failed' in VALID_TRANSITIONS['processing']
        assert 'paused' in VALID_TRANSITIONS['processing']

    def test_invalid_transition(self):
        from shared.infrastructure.config.queue import VALID_TRANSITIONS
        assert 'done' not in VALID_TRANSITIONS['pending']
        assert 'processing' not in VALID_TRANSITIONS['pending']


class TestEnqueue:
    def test_enqueue_job(self, queue):
        mgr, sa_session = queue
        pid = _insert_job(sa_session, 'https://example.com', 'pending')

        mgr.enqueue(pid)
        row = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.status == 'queued'
        assert row.queue_order > 0

    def test_enqueue_company(self, queue):
        mgr, sa_session = queue
        pid = _insert_company(sa_session, 'TestCorp', 'pending')

        mgr.enqueue(pid, table='pending_companies')
        row = sa_session.query(PendingCompanyModel).filter(PendingCompanyModel.id == pid).first()
        assert row.status == 'queued'

    def test_enqueue_bulk(self, queue):
        mgr, sa_session = queue
        ids = [_insert_job(sa_session, f'https://example{i}.com') for i in range(5)]

        mgr.enqueue_bulk(ids)
        rows = sa_session.query(PendingJobModel).filter(PendingJobModel.id.in_(ids)).all()
        assert all(r.status == 'queued' for r in rows)
        orders = [r.queue_order for r in rows]
        assert orders == sorted(orders)  # FIFO order preserved


class TestCancelJob:
    def test_cancel_queued(self, queue):
        mgr, sa_session = queue
        pid = _insert_job(sa_session, 'https://example.com', 'queued')

        ok = mgr.cancel_job(pid)
        assert ok
        row = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.status == 'pending'

    def test_cancel_nonexistent(self, queue):
        mgr, _ = queue
        assert not mgr.cancel_job(999)

    def test_cancel_processing_without_process(self, queue):
        """Cancel a 'processing' job when no subprocess exists — should set paused."""
        mgr, sa_session = queue
        pid = _insert_job(sa_session, 'https://example.com', 'processing')

        ok = mgr.cancel_job(pid)
        assert ok
        row = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.status == 'paused'


class TestResetJob:
    def test_reset_processing(self, queue):
        mgr, sa_session = queue
        pid = _insert_job(sa_session, 'https://example.com', 'processing')
        job = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        job.step_fetch = 1
        job.step_analyze = 1
        sa_session.commit()

        ok = mgr.reset_job(pid)
        assert ok
        row = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.status == 'queued'
        assert row.step_fetch == 0
        assert row.step_analyze == 0
        assert row.step_done == 0

    def test_reset_company(self, queue):
        mgr, sa_session = queue
        pid = _insert_company(sa_session, 'TestCorp', 'processing')
        comp = sa_session.query(PendingCompanyModel).filter(PendingCompanyModel.id == pid).first()
        comp.step_fetch = 1
        sa_session.commit()

        ok = mgr.reset_job(pid, table='pending_companies')
        assert ok
        row = sa_session.query(PendingCompanyModel).filter(PendingCompanyModel.id == pid).first()
        assert row.status == 'queued'
        assert row.step_fetch == 0

    def test_reset_nonexistent(self, queue):
        mgr, _ = queue
        assert not mgr.reset_job(999)


class TestDequeue:
    def test_dequeue(self, queue):
        mgr, sa_session = queue
        pid = _insert_job(sa_session, 'https://example.com', 'queued')

        mgr.dequeue(pid)
        row = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.status == 'pending'
        assert row.queue_order == 0


class TestGetStatus:
    def test_empty_queue(self, queue):
        mgr, _ = queue
        status = mgr.get_status()
        assert status['processing_count'] == 0
        assert status['queued_count'] == 0
        assert status['pending_count'] == 0
        assert status['concurrency'] == 2
        assert status['running'] is False

    def test_with_items(self, queue):
        mgr, sa_session = queue
        _insert_job(sa_session, 'https://a.com', 'pending')
        _insert_job(sa_session, 'https://b.com', 'queued')
        _insert_job(sa_session, 'https://c.com', 'processing')

        status = mgr.get_status()
        assert status['pending_count'] == 1
        assert status['queued_count'] == 1
        assert status['processing_count'] == 1


class TestMarkProcessingAsPaused:
    def test_marks_processing_as_paused(self, queue):
        mgr, sa_session = queue
        _insert_job(sa_session, 'https://a.com', 'processing')
        _insert_job(sa_session, 'https://b.com', 'processing')
        _insert_job(sa_session, 'https://c.com', 'queued')

        mgr._mark_processing_as_paused()
        rows = sa_session.query(PendingJobModel).order_by(PendingJobModel.id).all()
        statuses = [r.status for r in rows]
        assert statuses.count('paused') == 2
        assert statuses.count('queued') == 1


class TestOrphanRecovery:
    def test_reset_orphans(self, queue):
        mgr, sa_session = queue
        _insert_job(sa_session, 'https://a.com', 'processing')
        _insert_job(sa_session, 'https://b.com', 'processing')

        mgr._reset_processing_orphans()
        rows = sa_session.query(PendingJobModel).all()
        assert all(r.status == 'queued' for r in rows)


class TestGracefulShutdown:
    def test_stop_sets_running_false(self, queue):
        mgr, _ = queue
        mgr._running = True
        mgr.stop(timeout=1)
        assert not mgr._running
