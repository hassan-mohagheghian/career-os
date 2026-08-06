"""
Backward-compatible queue manager — delegates to the TaskIQ client.

This module exists for backward compatibility during the ARQ → TaskIQ migration.
New code should use `shared.infrastructure.taskiq.client` directly.
"""

from __future__ import annotations

import os
from datetime import datetime, UTC
from typing import Optional

from shared.infrastructure.process.logging_config import get_logger

logger = get_logger('queue')


class JobQueueManager:
    """Backward-compatible queue manager that delegates to TaskIQ."""

    def __init__(self, concurrency: int = 1):
        self._running = False
        self._concurrency = concurrency

    def start(self):
        self._running = True
        logger.info("[queue] TaskIQ-based — started")

    def stop(self, timeout: float = 15.0):
        self._running = False
        logger.info("[queue] TaskIQ-based — stopped")

    def enqueue(self, item_id: int, entity_type: str = 'job'):
        """Legacy enqueue — job processing now uses the ProcessingExecution flow."""
        logger.info(f"[queue] Legacy enqueue ignored for {entity_type} {item_id}")

    def enqueue_bulk(self, ids: list):
        """Legacy bulk enqueue for jobs is no longer supported."""
        logger.info("[queue] Job bulk enqueue removed — use ProcessingExecution")

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
        """Legacy callback — no-op."""
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
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = JobQueueManager()
        _queue_manager.start()
    return _queue_manager
