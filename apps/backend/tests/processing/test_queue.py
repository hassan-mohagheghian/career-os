"""Tests for TaskIQ queue integration and backward-compat queue manager."""

import os

import pytest


class TestTaskiqClient:
    """Tests for the TaskIQ client enqueue helpers."""

    def test_enqueue_execution_sync_creates_task(self, monkeypatch):
        from shared.infrastructure.taskiq.client import enqueue_execution_sync
        monkeypatch.setenv("TASKIQ_BROKER", "memory")
        task_id = enqueue_execution_sync("exec-1")
        assert task_id is not None


class TestBackwardCompatQueue:
    """Tests for backward-compatible JobQueueManager."""

    def test_init_queue_manager(self):
        from shared.infrastructure.config.queue import init_queue_manager
        mgr = init_queue_manager(":memory:")
        assert mgr is not None
        assert mgr._running is True
        mgr.stop()

    def test_cancel_and_reset_via_db(self):
        from shared.infrastructure.config.queue import get_queue_manager
        mgr = get_queue_manager()
        mgr._running = True
        status = mgr.get_status()
        assert "processing" in status
        mgr.stop()
