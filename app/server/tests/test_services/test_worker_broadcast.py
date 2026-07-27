"""Tests for worker broadcasting — real-time SocketIO events during processing."""

import os
import sqlite3
import tempfile
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.process.models import StatusUpdate, LogEntry, ProcessingComplete, ProcessingError
from infrastructure.database.sqlalchemy_config import Base
import infrastructure.database.models.pending_model


@pytest.fixture
def sa_test_db():
    """Create a temp DB with SA schema, return (path, sa_session)."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield path, session
    session.close()
    engine.dispose()
    os.remove(path)


INSERT_JOB = """
    INSERT INTO pending_jobs (url, source, status, notes, links, workflow_log,
        version, step_fetch, step_analyze, step_resume, step_cover, step_db,
        step_done, queue_order, step_extract_raw, step_extract_struct)
    VALUES (?, 'cli', ?, '[]', '[]', '[]',
        1, 0, 0, 0, 0, 0,
        0, 0, 0, 0)
"""

INSERT_COMPANY = """
    INSERT INTO pending_companies (input_text, source, status, notes, links,
        input_type, workflow_log, version, step_fetch, step_extract,
        step_analyze, step_save, step_done)
    VALUES (?, 'web', ?, '[]', '[]',
        'url', '[]', 1, 0, 0,
        0, 0, 0)
"""


# ── Worker Broadcasting Tests ──────────────────────────────────────


class TestWorkerBroadcasting:
    """Test that worker.py emits SocketIO events via broadcaster."""

    def test_update_step_emits_event(self, sa_test_db):
        path, sa_session = sa_test_db
        conn = sqlite3.connect(path)
        conn.execute(INSERT_JOB, ('https://example.com/job', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.worker.get_session_sync', return_value=sa_session), \
             patch('services.worker.broadcaster', mock_broadcaster):
            from services.worker import _update_step
            _update_step(1, 'step_fetch', 1)

            mock_broadcaster.step_update.assert_called_once()
            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.table == 'pending_jobs'
            assert event.pid == 1
            assert event.step == 'step_fetch'
            assert event.val == 1

    def test_update_step_with_status_emits_extra(self, sa_test_db):
        path, sa_session = sa_test_db
        conn = sqlite3.connect(path)
        conn.execute(INSERT_JOB, ('https://example.com/job', 'queued'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.worker.get_session_sync', return_value=sa_session), \
             patch('services.worker.broadcaster', mock_broadcaster):
            from services.worker import _update_step
            _update_step(1, 'step_fetch', 0, status='processing')

            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.val == 0
            assert event.extra['status'] == 'processing'

    def test_log_emits_event(self, sa_test_db):
        path, sa_session = sa_test_db
        conn = sqlite3.connect(path)
        conn.execute(INSERT_JOB, ('https://example.com/job', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.worker.get_session_sync', return_value=sa_session), \
             patch('services.worker.broadcaster', mock_broadcaster):
            from services.worker import _log
            _log(1, 'fetch', 'Fetching page...')

            mock_broadcaster.log.assert_called_once()
            event = mock_broadcaster.log.call_args[0][0]
            assert event.table == 'pending_jobs'
            assert event.pid == 1
            assert event.step == 'fetch'
            assert event.msg == 'Fetching page...'

    def test_fail_emits_error_event(self, sa_test_db):
        path, sa_session = sa_test_db
        conn = sqlite3.connect(path)
        conn.execute(INSERT_JOB, ('https://example.com/job', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.worker.get_session_sync', return_value=sa_session), \
             patch('services.worker.broadcaster', mock_broadcaster):
            from services.worker import _fail
            _fail(1, 'Network timeout', step='fetch')

            mock_broadcaster.error.assert_called_once()
            event = mock_broadcaster.error.call_args[0][0]
            assert event.table == 'pending_jobs'
            assert event.pid == 1
            assert 'Network timeout' in event.msg
            assert event.step == 'fetch'

    def test_save_session_id_persists_and_broadcasts(self, sa_test_db):
        path, sa_session = sa_test_db
        conn = sqlite3.connect(path)
        conn.execute(INSERT_JOB, ('https://example.com/job', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.worker.get_session_sync', return_value=sa_session), \
             patch('services.worker.broadcaster', mock_broadcaster):
            from services.worker import _save_session_id
            _save_session_id(1, 'sess_abc123')

            conn = sqlite3.connect(path)
            row = conn.execute("SELECT session_id FROM pending_jobs WHERE id=1").fetchone()
            conn.close()
            assert row[0] == 'sess_abc123'

            mock_broadcaster.step_update.assert_called_once()
            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.step == 'session_id'
            assert event.extra['session_id'] == 'sess_abc123'


class TestCompanyWorkerBroadcasting:
    """Test that company_worker.py emits SocketIO events via broadcaster."""

    def test_update_step_emits_event(self, sa_test_db):
        path, sa_session = sa_test_db
        conn = sqlite3.connect(path)
        conn.execute(INSERT_COMPANY, ('https://example.com/company', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.company_worker.get_session_sync', return_value=sa_session), \
             patch('services.company_worker.broadcaster', mock_broadcaster):
            from services.company_worker import _update_step
            _update_step(1, 'step_fetch', 1)

            mock_broadcaster.step_update.assert_called_once()
            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.table == 'pending_companies'
            assert event.pid == 1
            assert event.step == 'step_fetch'
            assert event.val == 1

    def test_update_step_with_status_emits_extra(self, sa_test_db):
        path, sa_session = sa_test_db
        conn = sqlite3.connect(path)
        conn.execute(INSERT_COMPANY, ('https://example.com/company', 'queued'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.company_worker.get_session_sync', return_value=sa_session), \
             patch('services.company_worker.broadcaster', mock_broadcaster):
            from services.company_worker import _update_step
            _update_step(1, 'step_fetch', 0, status='processing')

            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.val == 0
            assert event.extra['status'] == 'processing'

    def test_log_emits_event(self, sa_test_db):
        path, sa_session = sa_test_db
        conn = sqlite3.connect(path)
        conn.execute(INSERT_COMPANY, ('https://example.com/company', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.company_worker.get_session_sync', return_value=sa_session), \
             patch('services.company_worker.broadcaster', mock_broadcaster):
            from services.company_worker import _log
            _log(1, 'fetch', 'Fetching URL...')

            mock_broadcaster.log.assert_called_once()
            event = mock_broadcaster.log.call_args[0][0]
            assert event.table == 'pending_companies'
            assert event.pid == 1
            assert event.step == 'fetch'
            assert event.msg == 'Fetching URL...'

    def test_fail_emits_error_event(self, sa_test_db):
        path, sa_session = sa_test_db
        conn = sqlite3.connect(path)
        conn.execute(INSERT_COMPANY, ('https://example.com/company', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.company_worker.get_session_sync', return_value=sa_session), \
             patch('services.company_worker.broadcaster', mock_broadcaster):
            from services.company_worker import _fail
            _fail(1, 'Page not found', step='fetch')

            mock_broadcaster.error.assert_called_once()
            event = mock_broadcaster.error.call_args[0][0]
            assert event.table == 'pending_companies'
            assert event.pid == 1
            assert 'Page not found' in event.msg
            assert event.step == 'fetch'

    def test_save_session_id_persists_and_broadcasts(self, sa_test_db):
        path, sa_session = sa_test_db
        conn = sqlite3.connect(path)
        conn.execute(INSERT_COMPANY, ('https://example.com/company', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.company_worker.get_session_sync', return_value=sa_session), \
             patch('services.company_worker.broadcaster', mock_broadcaster):
            from services.company_worker import _save_session_id
            _save_session_id(1, 'sess_xyz789')

            conn = sqlite3.connect(path)
            row = conn.execute("SELECT session_id FROM pending_companies WHERE id=1").fetchone()
            conn.close()
            assert row[0] == 'sess_xyz789'

            mock_broadcaster.step_update.assert_called_once()
            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.step == 'session_id'
            assert event.extra['session_id'] == 'sess_xyz789'


class TestBroadcasterLogging:
    """Test that broadcaster logs events for audit trail."""

    def test_step_update_logs(self, caplog):
        from services.process.broadcaster import Broadcaster
        b = Broadcaster()
        mock_sio = MagicMock()
        mock_sio.emit = AsyncMock()
        b.set_socketio(mock_sio)

        with caplog.at_level('INFO', logger='services.process.broadcaster'):
            b.step_update(StatusUpdate(table='pending_jobs', pid=42, step='step_fetch', val=1))

        assert any('[ws] pending:update' in r.message for r in caplog.records)
        assert any('id=42' in r.message for r in caplog.records)

    def test_log_event_logs(self, caplog):
        from services.process.broadcaster import Broadcaster
        b = Broadcaster()
        mock_sio = MagicMock()
        mock_sio.emit = AsyncMock()
        b.set_socketio(mock_sio)

        with caplog.at_level('INFO', logger='services.process.broadcaster'):
            b.log(LogEntry(table='pending_jobs', pid=10, step='fetch', msg='Done'))

        assert any('[ws] pending:log' in r.message for r in caplog.records)

    def test_complete_logs(self, caplog):
        from services.process.broadcaster import Broadcaster
        b = Broadcaster()
        mock_sio = MagicMock()
        mock_sio.emit = AsyncMock()
        b.set_socketio(mock_sio)

        with caplog.at_level('INFO', logger='services.process.broadcaster'):
            b.complete(ProcessingComplete(table='pending_jobs', pid=10, result={'num': 99}))

        assert any('[ws] pending:complete' in r.message for r in caplog.records)

    def test_error_logs(self, caplog):
        from services.process.broadcaster import Broadcaster
        b = Broadcaster()
        mock_sio = MagicMock()
        mock_sio.emit = AsyncMock()
        b.set_socketio(mock_sio)

        with caplog.at_level('ERROR', logger='services.process.broadcaster'):
            b.error(ProcessingError(table='pending_jobs', pid=10, msg='boom', step='fetch'))

        assert any('[ws] pending:error' in r.message for r in caplog.records)
