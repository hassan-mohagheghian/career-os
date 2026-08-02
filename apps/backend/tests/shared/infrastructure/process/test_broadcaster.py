"""Tests for Broadcaster — observer pattern for status delivery."""

import pytest
from unittest.mock import MagicMock, call, AsyncMock
from shared.infrastructure.process.broadcaster import Broadcaster
from shared.infrastructure.process.models import (
    StatusUpdate, LogEntry, ProcessingComplete, ProcessingError,
)


class TestBroadcaster:
    def setup_method(self):
        self.b = Broadcaster()
        self.mock_socketio = MagicMock()
        self.mock_socketio.emit = AsyncMock()
        self.b.set_socketio(self.mock_socketio)

    def test_step_update_emits_to_room(self):
        event = StatusUpdate(table='pending_jobs', pid=42, step='step_fetch', val=1)
        self.b.step_update(event)
        self.mock_socketio.emit.assert_called_once()
        args = self.mock_socketio.emit.call_args
        assert args[0][0] == 'pending:update'
        assert args[0][1]['id'] == 42
        assert args[0][1]['step'] == 'step_fetch'
        assert args[1]['room'] == 'job_42'

    def test_step_update_company_table(self):
        event = StatusUpdate(table='pending_companies', pid=5, step='step_extract', val=1)
        self.b.step_update(event)
        args = self.mock_socketio.emit.call_args
        assert args[0][0] == 'company:update'
        assert args[1]['room'] == 'company_5'

    def test_log_emits(self):
        event = LogEntry(table='pending_jobs', pid=10, step='fetch', msg='Done')
        self.b.log(event)
        args = self.mock_socketio.emit.call_args
        assert args[0][0] == 'pending:log'
        assert args[0][1]['msg'] == 'Done'

    def test_complete_emits(self):
        event = ProcessingComplete(table='pending_jobs', pid=10, result={'num': 99})
        self.b.complete(event)
        args = self.mock_socketio.emit.call_args
        assert args[0][0] == 'pending:complete'
        assert args[0][1]['num'] == 99

    def test_error_emits(self):
        event = ProcessingError(table='pending_jobs', pid=10, msg='boom', step='fetch')
        self.b.error(event)
        args = self.mock_socketio.emit.call_args
        assert args[0][0] == 'pending:error'
        assert '[fetch] boom' in args[0][1]['msg']

    def test_queue_status_broadcasts(self):
        self.b.queue_status(processing=2, queued=5, pending=3, concurrency=4)
        args = self.mock_socketio.emit.call_args
        assert args[0][0] == 'queue:status'
        assert args[0][1]['processing'] == 2

    def test_listener_receives_events(self):
        received = []
        self.b.add_listener(lambda event_type, data: received.append((event_type, data)))
        event = StatusUpdate(table='pending_jobs', pid=1, step='step_fetch', val=1)
        self.b.step_update(event)
        assert len(received) == 1
        assert received[0][0] == 'step_update'

    def test_no_socketio_still_works(self):
        self.b.set_socketio(None)
        event = StatusUpdate(table='pending_jobs', pid=1, step='step_fetch', val=1)
        # Should not raise
        self.b.step_update(event)

    def test_listener_exception_doesnt_break(self):
        def bad_listener(event_type, data):
            raise RuntimeError("oops")
        self.b.add_listener(bad_listener)
        event = StatusUpdate(table='pending_jobs', pid=1, step='step_fetch', val=1)
        # Should not raise
        self.b.step_update(event)
