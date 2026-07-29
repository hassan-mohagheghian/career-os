"""
Backward-compatible queue manager — delegates to ARQ.

This module exists for backward compatibility during the ARQ migration.
New code should use `shared.infrastructure.queue.arq_client` directly.
"""

from __future__ import annotations

import os
from datetime import datetime, UTC
from typing import Optional

from shared.infrastructure.process.logging_config import get_logger

logger = get_logger('queue')


class JobQueueManager:
    """Backward-compatible queue manager that delegates to ARQ."""

    def __init__(self):
        self._running = False

    def start(self):
        self._running = True
        logger.info("[queue] ARQ-based — started (delegating to ARQ)")

    def stop(self, timeout: float = 15.0):
        self._running = False
        logger.info("[queue] ARQ-based — stopped")

    def enqueue(self, item_id: int, entity_type: str = 'job'):
        from shared.infrastructure.queue.arq_client import enqueue_job_sync, enqueue_company_sync
        if entity_type == 'job':
            enqueue_job_sync(item_id)
        else:
            enqueue_company_sync(item_id)
        logger.info(f"[queue] Enqueued {entity_type} {item_id} via ARQ")

    def enqueue_bulk(self, ids: list):
        from shared.infrastructure.queue.arq_client import enqueue_job_sync
        for pid in ids:
            enqueue_job_sync(pid)
        logger.info(f"[queue] Enqueued {len(ids)} items via ARQ")

    def cancel_item(self, item_id: int, entity_type: str = 'job'):
        session = None
        try:
            from shared.infrastructure.database.session import get_session_sync
            session = get_session_sync()
            now = datetime.now(UTC).isoformat()
            if entity_type == 'job':
                from jobs.infrastructure import SQLAlchemyJobRepository
                repo = SQLAlchemyJobRepository(session)
                repo.update_fields(item_id, status='cancelled', updated_at=now)
            else:
                from companies.infrastructure import SQLAlchemyCompanyRepository
                repo = SQLAlchemyCompanyRepository(session)
                repo.update_fields(item_id, status='cancelled', updated_at=now)
            logger.info(f"[queue] Cancelled {entity_type} {item_id}")
            return True
        finally:
            if session:
                session.close()

    def reset_item(self, item_id: int, entity_type: str = 'job') -> bool:
        session = None
        try:
            from shared.infrastructure.database.session import get_session_sync
            session = get_session_sync()
            now = datetime.now(UTC).isoformat()
            if entity_type == 'job':
                from jobs.infrastructure import SQLAlchemyJobRepository
                repo = SQLAlchemyJobRepository(session)
                repo.update_fields(item_id, status='pending', error=None, current_node=None,
                    progress_pct=0, retry_count=0, failure_reason=None,
                    failure_step=None, failure_timestamp=None, updated_at=now)
            else:
                from companies.infrastructure import SQLAlchemyCompanyRepository
                repo = SQLAlchemyCompanyRepository(session)
                repo.update_fields(item_id, status='pending', error=None, current_node=None,
                    progress_pct=0, retry_count=0, failure_reason=None,
                    failure_step=None, failure_timestamp=None, updated_at=now)
            logger.info(f"[queue] Reset {entity_type} {item_id}")
            return True
        finally:
            if session:
                session.close()

    def signal_job_done(self, item_id: int, entity_type: str = 'job'):
        """Legacy callback — no-op with ARQ."""
        pass

    def cancel_job(self, job_id, table='pending_jobs'):
        """Legacy cancel — delegates to cancel_item."""
        return self.cancel_item(int(job_id), entity_type='job')

    def reset_job(self, job_id, table='pending_jobs'):
        """Legacy reset — delegates to reset_item."""
        return self.reset_item(int(job_id), entity_type='job')

    def get_status(self) -> dict:
        return {
            "processing": [],
            "queued_count": 0,
            "pending_count": 0,
            "concurrency": 0,
            "running": self._running,
        }


_queue_manager: Optional[JobQueueManager] = None


def init_queue_manager(db_path: str) -> JobQueueManager:
    global _queue_manager
    _queue_manager = JobQueueManager()
    _queue_manager.start()
    return _queue_manager


def get_queue_manager() -> JobQueueManager:
    if _queue_manager is None:
        _queue_manager = JobQueueManager()
        _queue_manager.start()
    return _queue_manager
