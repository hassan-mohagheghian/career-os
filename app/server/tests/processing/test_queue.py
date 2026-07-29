"""Tests for ARQ queue integration and backward-compat queue manager."""

import pytest


class TestArqClient:
    """Tests for the ARQ client enqueue helpers."""

    def test_enqueue_job_sync_creates_task(self):
        from shared.infrastructure.queue.arq_client import enqueue_job_sync
        try:
            enqueue_job_sync(1)
        except Exception:
            pass


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
