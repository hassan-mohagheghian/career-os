"""Tests for JobQueueManager — graceful shutdown, cancel, reset, transitions."""

import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from jobs.infrastructure.models.job_model import JobModel
from companies.infrastructure.models.company_model import CompanyModel
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

_counter = 0
def _insert_job(session, url, status='pending'):
    global _counter
    _counter += 1
    m = JobModel(num=_counter, url=url, status=status, source='cli')
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.num


def _insert_company(session, text, status='pending'):
    m = CompanyModel(name=text, status=status, source='web')
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.id


class TestEnqueue:
    def test_enqueue_job(self, queue):
        mgr, sa_session = queue
        pid = _insert_job(sa_session, 'https://example.com', 'pending')

        mgr.enqueue(pid)
        row = sa_session.query(JobModel).filter(JobModel.num == pid).first()
        assert row.status == 'queued'
        assert row.queue_order > 0

    def test_enqueue_company(self, queue):
        mgr, sa_session = queue
        pid = _insert_company(sa_session, 'TestCorp', 'pending')

        mgr.enqueue(pid, entity_type='company')
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == pid).first()
        assert row.status == 'queued'


class TestCancelItem:
    def test_cancel_queued(self, queue):
        mgr, sa_session = queue
        pid = _insert_job(sa_session, 'https://example.com', 'queued')

        ok = mgr.cancel_item(pid)
        assert ok
        row = sa_session.query(JobModel).filter(JobModel.num == pid).first()
        assert row.status == 'cancelled'

    def test_cancel_nonexistent(self, queue):
        mgr, _ = queue
        assert not mgr.cancel_item(999)


class TestResetItem:
    def test_reset_processing(self, queue):
        mgr, sa_session = queue
        pid = _insert_job(sa_session, 'https://example.com', 'starting')

        ok = mgr.reset_item(pid)
        assert ok
        row = sa_session.query(JobModel).filter(JobModel.num == pid).first()
        assert row.status == 'pending'

    def test_reset_company(self, queue):
        mgr, sa_session = queue
        pid = _insert_company(sa_session, 'TestCorp', 'starting')

        ok = mgr.reset_item(pid, entity_type='company')
        assert ok
        row = sa_session.query(CompanyModel).filter(CompanyModel.id == pid).first()
        assert row.status == 'pending'

    def test_reset_nonexistent(self, queue):
        mgr, _ = queue
        assert not mgr.reset_item(999)


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
        assert status['pending_count'] >= 1
        assert status['queued_count'] >= 1
        assert status['processing_count'] >= 1


class TestGracefulShutdown:
    def test_stop_sets_running_false(self, queue):
        mgr, _ = queue
        mgr._running = True
        mgr.stop(timeout=1)
        assert not mgr._running
