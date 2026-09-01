"""Tests for worker broadcasting — real-time SocketIO events during processing."""

import pytest
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.orm import sessionmaker
from shared.infrastructure.process.models import StatusUpdate, LogEntry, ProcessingComplete, ProcessingError
from shared.infrastructure.database.sqlalchemy_config import Base
from jobs.infrastructure.models.job_model import JobModel


@pytest.fixture
def sa_test_db(_engine):
    connection = _engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


_counter = 0
def _insert_pending_job(session, url, status):
    global _counter
    _counter += 1
    m = JobModel(id=str(uuid.uuid7()), url=url, source='cli', status=status, user_id="test-user")
    session.add(m)
    session.commit()
    session.refresh(m)
    return m.id


class TestWorkerBroadcasting:
    """Test that worker.py emits SocketIO events via broadcaster."""

    def test_update_step_emits_event(self, sa_test_db):
        pid = _insert_pending_job(sa_test_db, 'https://example.com/job', 'processing')
        mock_broadcaster = MagicMock()
        with patch('jobs.infrastructure.workers.worker.get_session_sync', return_value=sa_test_db), \
             patch('jobs.infrastructure.workers.worker.broadcaster', mock_broadcaster):
            from jobs.infrastructure.workers.worker import _update_step
            _update_step(pid, 'step_fetch', 1)
            mock_broadcaster.step_update.assert_called_once()
            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.table == 'job'
            assert event.pid == pid
            assert event.step == 'step_fetch'
            assert event.val == 1

    def test_update_step_with_status_emits_extra(self, sa_test_db):
        pid = _insert_pending_job(sa_test_db, 'https://example.com/job', 'queued')
        mock_broadcaster = MagicMock()
        with patch('jobs.infrastructure.workers.worker.get_session_sync', return_value=sa_test_db), \
             patch('jobs.infrastructure.workers.worker.broadcaster', mock_broadcaster):
            from jobs.infrastructure.workers.worker import _update_step
            _update_step(pid, 'step_fetch', 0, status='processing')
            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.val == 0
            assert event.extra['status'] == 'processing'

    def test_log_emits_event(self, sa_test_db):
        pid = _insert_pending_job(sa_test_db, 'https://example.com/job', 'processing')
        mock_broadcaster = MagicMock()
        with patch('jobs.infrastructure.workers.worker.get_session_sync', return_value=sa_test_db), \
             patch('jobs.infrastructure.workers.worker.broadcaster', mock_broadcaster):
            from jobs.infrastructure.workers.worker import _log
            _log(pid, 'fetch', 'Fetching page...')
            mock_broadcaster.log.assert_called_once()
            event = mock_broadcaster.log.call_args[0][0]
            assert event.table == 'job'
            assert event.pid == pid
            assert event.step == 'fetch'
            assert event.msg == 'Fetching page...'

    def test_fail_emits_error_event(self, sa_test_db):
        pid = _insert_pending_job(sa_test_db, 'https://example.com/job', 'processing')
        mock_broadcaster = MagicMock()
        with patch('jobs.infrastructure.workers.worker.get_session_sync', return_value=sa_test_db), \
             patch('jobs.infrastructure.workers.worker.broadcaster', mock_broadcaster):
            from jobs.infrastructure.workers.worker import _fail
            _fail(pid, 'Network timeout', step='fetch')
            mock_broadcaster.error.assert_called_once()
            event = mock_broadcaster.error.call_args[0][0]
            assert event.table == 'job'
            assert event.pid == pid
            assert 'Network timeout' in event.msg
            assert event.step == 'fetch'

    def test_save_session_id_persists_and_broadcasts(self, sa_test_db):
        pid = _insert_pending_job(sa_test_db, 'https://example.com/job', 'processing')
        mock_broadcaster = MagicMock()
        with patch('jobs.infrastructure.workers.worker.get_session_sync', return_value=sa_test_db), \
             patch('jobs.infrastructure.workers.worker.broadcaster', mock_broadcaster):
            from jobs.infrastructure.workers.worker import _save_session_id
            _save_session_id(pid, 'sess_abc123')
            row = sa_test_db.query(JobModel).filter(JobModel.id == pid).first()
            assert row.session_id == 'sess_abc123'
            mock_broadcaster.step_update.assert_called_once()
            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.step == 'session_id'
            assert event.extra['session_id'] == 'sess_abc123'


class TestBroadcasterLogging:
    """Test that broadcaster logs events for audit trail."""

    def test_step_update_logs(self, caplog):
        from shared.infrastructure.process.broadcaster import Broadcaster
        b = Broadcaster()
        mock_sio = MagicMock()
        mock_sio.emit = AsyncMock()
        b.set_socketio(mock_sio)
        with caplog.at_level('INFO', logger='shared.infrastructure.process.broadcaster'):
            b.step_update(StatusUpdate(table='pending_jobs', pid=42, step='step_fetch', val=1))
        assert any('[ws] pending:update' in r.message for r in caplog.records)
        assert any('id=42' in r.message for r in caplog.records)

    def test_log_event_logs(self, caplog):
        from shared.infrastructure.process.broadcaster import Broadcaster
        b = Broadcaster()
        mock_sio = MagicMock()
        mock_sio.emit = AsyncMock()
        b.set_socketio(mock_sio)
        with caplog.at_level('INFO', logger='shared.infrastructure.process.broadcaster'):
            b.log(LogEntry(table='pending_jobs', pid=10, step='fetch', msg='Done'))
        assert any('[ws] pending:log' in r.message for r in caplog.records)

    def test_complete_logs(self, caplog):
        from shared.infrastructure.process.broadcaster import Broadcaster
        b = Broadcaster()
        mock_sio = MagicMock()
        mock_sio.emit = AsyncMock()
        b.set_socketio(mock_sio)
        with caplog.at_level('INFO', logger='shared.infrastructure.process.broadcaster'):
            b.complete(ProcessingComplete(table='pending_jobs', pid=10, result={'num': 99}))
        assert any('[ws] pending:complete' in r.message for r in caplog.records)

    def test_error_logs(self, caplog):
        from shared.infrastructure.process.broadcaster import Broadcaster
        b = Broadcaster()
        mock_sio = MagicMock()
        mock_sio.emit = AsyncMock()
        b.set_socketio(mock_sio)
        with caplog.at_level('ERROR', logger='shared.infrastructure.process.broadcaster'):
            b.error(ProcessingError(table='pending_jobs', pid=10, msg='boom', step='fetch'))
        assert any('[ws] pending:error' in r.message for r in caplog.records)