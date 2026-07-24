"""Tests for worker broadcasting — real-time SocketIO events during processing."""

import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from services.process.models import StatusUpdate, LogEntry, ProcessingComplete, ProcessingError


def _make_db(path, row_factory=None):
    """Create a _db() function bound to a specific path."""
    def _db():
        conn = sqlite3.connect(path)
        conn.row_factory = row_factory
        return conn
    return _db


# ── Worker Broadcasting Tests ──────────────────────────────────────


class TestWorkerBroadcasting:
    """Test that worker.py emits SocketIO events via broadcaster."""

    def test_update_step_emits_event(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)", ('https://example.com/job', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.worker._db', _make_db(test_db, sqlite3.Row)), \
             patch('services.worker.broadcaster', mock_broadcaster):
            from services.worker import _update_step
            _update_step(1, 'step_fetch', 1)

            mock_broadcaster.step_update.assert_called_once()
            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.table == 'pending_jobs'
            assert event.pid == 1
            assert event.step == 'step_fetch'
            assert event.val == 1

    def test_update_step_with_status_emits_extra(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)", ('https://example.com/job', 'queued'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.worker._db', _make_db(test_db, sqlite3.Row)), \
             patch('services.worker.broadcaster', mock_broadcaster):
            from services.worker import _update_step
            _update_step(1, 'step_fetch', 0, status='processing')

            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.val == 0
            assert event.extra['status'] == 'processing'

    def test_log_emits_event(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)", ('https://example.com/job', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.worker._db', _make_db(test_db, sqlite3.Row)), \
             patch('services.worker.broadcaster', mock_broadcaster):
            from services.worker import _log
            _log(1, 'fetch', 'Fetching page...')

            mock_broadcaster.log.assert_called_once()
            event = mock_broadcaster.log.call_args[0][0]
            assert event.table == 'pending_jobs'
            assert event.pid == 1
            assert event.step == 'fetch'
            assert event.msg == 'Fetching page...'

    def test_fail_emits_error_event(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)", ('https://example.com/job', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.worker._db', _make_db(test_db, sqlite3.Row)), \
             patch('services.worker.broadcaster', mock_broadcaster):
            from services.worker import _fail
            _fail(1, 'Network timeout', step='fetch')

            mock_broadcaster.error.assert_called_once()
            event = mock_broadcaster.error.call_args[0][0]
            assert event.table == 'pending_jobs'
            assert event.pid == 1
            assert 'Network timeout' in event.msg
            assert event.step == 'fetch'

    def test_save_session_id_persists_and_broadcasts(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO pending_jobs (url, status) VALUES (?, ?)", ('https://example.com/job', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.worker._db', _make_db(test_db, sqlite3.Row)), \
             patch('services.worker.broadcaster', mock_broadcaster):
            from services.worker import _save_session_id
            _save_session_id(1, 'sess_abc123')

            conn = sqlite3.connect(test_db)
            row = conn.execute("SELECT session_id FROM pending_jobs WHERE id=1").fetchone()
            conn.close()
            assert row[0] == 'sess_abc123'

            mock_broadcaster.step_update.assert_called_once()
            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.step == 'session_id'
            assert event.extra['session_id'] == 'sess_abc123'


class TestCompanyWorkerBroadcasting:
    """Test that company_worker.py emits SocketIO events via broadcaster."""

    def test_update_step_emits_event(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO pending_companies (input_text, status) VALUES (?, ?)", ('https://example.com/company', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.company_worker._db', _make_db(test_db, sqlite3.Row)), \
             patch('services.company_worker.broadcaster', mock_broadcaster):
            from services.company_worker import _update_step
            _update_step(1, 'step_fetch', 1)

            mock_broadcaster.step_update.assert_called_once()
            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.table == 'pending_companies'
            assert event.pid == 1
            assert event.step == 'step_fetch'
            assert event.val == 1

    def test_update_step_with_status_emits_extra(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO pending_companies (input_text, status) VALUES (?, ?)", ('https://example.com/company', 'queued'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.company_worker._db', _make_db(test_db, sqlite3.Row)), \
             patch('services.company_worker.broadcaster', mock_broadcaster):
            from services.company_worker import _update_step
            _update_step(1, 'step_fetch', 0, status='processing')

            event = mock_broadcaster.step_update.call_args[0][0]
            assert event.val == 0
            assert event.extra['status'] == 'processing'

    def test_log_emits_event(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO pending_companies (input_text, status) VALUES (?, ?)", ('https://example.com/company', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.company_worker._db', _make_db(test_db, sqlite3.Row)), \
             patch('services.company_worker.broadcaster', mock_broadcaster):
            from services.company_worker import _log
            _log(1, 'fetch', 'Fetching URL...')

            mock_broadcaster.log.assert_called_once()
            event = mock_broadcaster.log.call_args[0][0]
            assert event.table == 'pending_companies'
            assert event.pid == 1
            assert event.step == 'fetch'
            assert event.msg == 'Fetching URL...'

    def test_fail_emits_error_event(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO pending_companies (input_text, status) VALUES (?, ?)", ('https://example.com/company', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.company_worker._db', _make_db(test_db, sqlite3.Row)), \
             patch('services.company_worker.broadcaster', mock_broadcaster):
            from services.company_worker import _fail
            _fail(1, 'Page not found', step='fetch')

            mock_broadcaster.error.assert_called_once()
            event = mock_broadcaster.error.call_args[0][0]
            assert event.table == 'pending_companies'
            assert event.pid == 1
            assert 'Page not found' in event.msg
            assert event.step == 'fetch'

    def test_save_session_id_persists_and_broadcasts(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO pending_companies (input_text, status) VALUES (?, ?)", ('https://example.com/company', 'processing'))
        conn.commit()
        conn.close()

        mock_broadcaster = MagicMock()
        with patch('services.company_worker._db', _make_db(test_db, sqlite3.Row)), \
             patch('services.company_worker.broadcaster', mock_broadcaster):
            from services.company_worker import _save_session_id
            _save_session_id(1, 'sess_xyz789')

            conn = sqlite3.connect(test_db)
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
        b.set_socketio(MagicMock())

        with caplog.at_level('INFO', logger='services.process.broadcaster'):
            b.step_update(StatusUpdate(table='pending_jobs', pid=42, step='step_fetch', val=1))

        assert any('[ws] pending:update' in r.message for r in caplog.records)
        assert any('id=42' in r.message for r in caplog.records)

    def test_log_event_logs(self, caplog):
        from services.process.broadcaster import Broadcaster
        b = Broadcaster()
        b.set_socketio(MagicMock())

        with caplog.at_level('INFO', logger='services.process.broadcaster'):
            b.log(LogEntry(table='pending_jobs', pid=10, step='fetch', msg='Done'))

        assert any('[ws] pending:log' in r.message for r in caplog.records)

    def test_complete_logs(self, caplog):
        from services.process.broadcaster import Broadcaster
        b = Broadcaster()
        b.set_socketio(MagicMock())

        with caplog.at_level('INFO', logger='services.process.broadcaster'):
            b.complete(ProcessingComplete(table='pending_jobs', pid=10, result={'num': 99}))

        assert any('[ws] pending:complete' in r.message for r in caplog.records)

    def test_error_logs(self, caplog):
        from services.process.broadcaster import Broadcaster
        b = Broadcaster()
        b.set_socketio(MagicMock())

        with caplog.at_level('ERROR', logger='services.process.broadcaster'):
            b.error(ProcessingError(table='pending_jobs', pid=10, msg='boom', step='fetch'))

        assert any('[ws] pending:error' in r.message for r in caplog.records)
