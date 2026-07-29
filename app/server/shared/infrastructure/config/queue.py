"""
Persistent concurrent job/company queue manager.

Processes up to N jobs and N companies concurrently from the
status-based lifecycle on jobs/companies tables.
N is controlled by QUEUE_CONCURRENCY env var (default 2 per type).

Status flow:
    pending -> queued -> processing -> completed
                                   -> failed
                                   -> cancelled

Features:
- Separate concurrency limits for jobs and companies (max 2 each)
- Per-item cancellation
- Per-item reset
- Automatic dequeue on completion
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, UTC
from typing import Any, Optional

from sqlalchemy import func
from jobs.infrastructure.models.job_model import JobModel
from shared.infrastructure.database.session import get_session_sync
from shared.domain.lifecycle import LifecycleStatus
from shared.infrastructure.process.logging_config import get_logger

logger = get_logger('queue')

CONCURRENCY = int(os.environ.get("QUEUE_CONCURRENCY", "2"))


class JobQueueManager:
    """Persistent concurrent queue for jobs and companies using status-based lifecycle."""

    def __init__(self, concurrency: int = CONCURRENCY):
        self._concurrency = concurrency
        self._running = False
        self._workers: list[threading.Thread] = []
        self._slot_event = threading.Event()
        self._shutdown_event = threading.Event()

    def start(self):
        if self._running:
            return
        self._running = True
        self._recover_orphans()

        for i in range(self._concurrency):
            t = threading.Thread(target=self._worker_loop, daemon=True, name=f"queue-{i}")
            self._workers.append(t)
            t.start()

        logger.info(f"[queue] Started {self._concurrency} workers")

    def stop(self, timeout: float = 15.0):
        if not self._running:
            return
        logger.info("[queue] Shutting down...")
        self._running = False
        self._slot_event.set()

        for t in self._workers:
            t.join(timeout=timeout / len(self._workers) if self._workers else timeout)

        self._mark_processing_as_failed()
        self._shutdown_event.set()
        logger.info("[queue] Shutdown complete")

    def enqueue(self, item_id: int, entity_type: str = 'job'):
        session = get_session_sync()
        try:
            now = datetime.now(UTC).isoformat()
            if entity_type == 'job':
                from jobs.infrastructure import SQLAlchemyJobRepository
                repo = SQLAlchemyJobRepository(session)
                order = (session.query(
                    func.coalesce(func.max(JobModel.queue_order), 0) + 1
                ).filter(JobModel.status == 'queued').scalar() or 0) + 1
                repo.update_fields(item_id, status='queued', queue_order=order, error=None, updated_at=now)
                logger.info(f"[queue] Enqueued job {item_id} (order={order})")
            else:
                from companies.infrastructure import SQLAlchemyCompanyRepository
                repo = SQLAlchemyCompanyRepository(session)
                repo.update_fields(item_id, status='queued', error=None, updated_at=now)
                logger.info(f"[queue] Enqueued company {item_id}")
        finally:
            session.close()
        self._slot_event.set()

    def cancel_item(self, item_id: int, entity_type: str = 'job') -> bool:
        session = get_session_sync()
        try:
            if entity_type == 'job':
                from jobs.infrastructure import SQLAlchemyJobRepository
                repo = SQLAlchemyJobRepository(session)
                item = repo.get_by_num(item_id)
                if not item:
                    return False
                repo.update_fields(item_id, status='cancelled', updated_at=datetime.now(UTC).isoformat())
            else:
                from companies.infrastructure import SQLAlchemyCompanyRepository
                repo = SQLAlchemyCompanyRepository(session)
                item = repo.get_by_id(item_id)
                if not item:
                    return False
                repo.update_fields(item_id, status='cancelled', updated_at=datetime.now(UTC).isoformat())
            logger.info(f"[queue] Cancelled {entity_type} {item_id}")
            return True
        finally:
            session.close()

    def reset_item(self, item_id: int, entity_type: str = 'job') -> bool:
        session = get_session_sync()
        try:
            now = datetime.now(UTC).isoformat()
            if entity_type == 'job':
                from jobs.infrastructure import SQLAlchemyJobRepository
                repo = SQLAlchemyJobRepository(session)
                item = repo.get_by_num(item_id)
                if not item:
                    return False
                repo.update_fields(
                    item_id, status='pending', error=None, current_node=None,
                    progress_pct=0, retry_count=0, failure_reason=None,
                    failure_step=None, failure_timestamp=None, session_id=None,
                    updated_at=now,
                )
            else:
                from companies.infrastructure import SQLAlchemyCompanyRepository
                repo = SQLAlchemyCompanyRepository(session)
                item = repo.get_by_id(item_id)
                if not item:
                    return False
                repo.update_fields(
                    item_id, status='pending', error=None, current_node=None,
                    progress_pct=0, retry_count=0, failure_reason=None,
                    failure_step=None, failure_timestamp=None, session_id=None,
                    updated_at=now,
                )
            logger.info(f"[queue] Reset {entity_type} {item_id}")
            return True
        finally:
            session.close()

    def get_status(self) -> dict:
        session = get_session_sync()
        try:
            from jobs.infrastructure import SQLAlchemyJobRepository
            from companies.infrastructure import SQLAlchemyCompanyRepository
            job_repo = SQLAlchemyJobRepository(session)
            company_repo = SQLAlchemyCompanyRepository(session)

            return {
                "processing": [{"num": r["num"], "company": r.get("company"), "url": r.get("url")} for r in job_repo.get_processing_items()],
                "processing_count": job_repo.get_processing_count(),
                "queued_count": job_repo.get_queued_count(),
                "pending_count": len(job_repo.list_by_status('pending')),
                "company_processing_count": company_repo.get_processing_count(),
                "company_queued_count": company_repo.get_queued_count(),
                "company_pending_count": len(company_repo.list_by_status('pending')),
                "concurrency": self._concurrency,
                "running": self._running,
            }
        finally:
            session.close()

    # ── Internal ───────────────────────────────────────────────────

    def _recover_orphans(self):
        session = get_session_sync()
        try:
            from jobs.infrastructure import SQLAlchemyJobRepository
            from companies.infrastructure import SQLAlchemyCompanyRepository
            now = datetime.now(UTC).isoformat()

            job_repo = SQLAlchemyJobRepository(session)
            stuck_jobs = job_repo.get_processing_items()
            for job in stuck_jobs:
                job_repo.update_fields(
                    job['num'], status='failed', error='Interrupted by server restart',
                    failure_reason='Server restart', failure_timestamp=now,
                    updated_at=now,
                )
            if stuck_jobs:
                logger.info(f"[queue] Recovered {len(stuck_jobs)} orphaned jobs")

            company_repo = SQLAlchemyCompanyRepository(session)
            stuck_companies = company_repo.get_processing_items()
            for company in stuck_companies:
                company_repo.update_fields(
                    company['id'], status='failed', error='Interrupted by server restart',
                    failure_reason='Server restart', failure_timestamp=now,
                    updated_at=now,
                )
            if stuck_companies:
                logger.info(f"[queue] Recovered {len(stuck_companies)} orphaned companies")
        finally:
            session.close()

    def _mark_processing_as_failed(self):
        session = get_session_sync()
        try:
            from jobs.infrastructure import SQLAlchemyJobRepository
            from companies.infrastructure import SQLAlchemyCompanyRepository
            now = datetime.now(UTC).isoformat()

            job_repo = SQLAlchemyJobRepository(session)
            for job in job_repo.get_processing_items():
                job_repo.update_fields(
                    job['num'], status='failed', error='Server shutdown',
                    failure_reason='Server shutdown', failure_timestamp=now,
                    updated_at=now,
                )

            company_repo = SQLAlchemyCompanyRepository(session)
            for company in company_repo.get_processing_items():
                company_repo.update_fields(
                    company['id'], status='failed', error='Server shutdown',
                    failure_reason='Server shutdown', failure_timestamp=now,
                    updated_at=now,
                )
        finally:
            session.close()

    def _pick_and_claim(self) -> Optional[dict]:
        session = get_session_sync()
        try:
            from jobs.infrastructure import SQLAlchemyJobRepository
            from companies.infrastructure import SQLAlchemyCompanyRepository

            job_repo = SQLAlchemyJobRepository(session)
            company_repo = SQLAlchemyCompanyRepository(session)

            job_processing = job_repo.get_processing_count()
            company_processing = company_repo.get_processing_count()

            if job_processing < self._concurrency:
                item = job_repo.pick_queued_item()
                if item:
                    item['entity_type'] = 'job'
                    return item

            if company_processing < self._concurrency:
                item = company_repo.pick_queued_item()
                if item:
                    item['entity_type'] = 'company'
                return item

            return None
        finally:
            session.close()

    def _worker_loop(self):
        while self._running:
            try:
                item = self._pick_and_claim()

                if not item:
                    self._slot_event.clear()
                    self._slot_event.wait(timeout=2.0)
                    continue

                pid = item.get('num') or item.get('id')
                entity_type = item.get('entity_type', 'job')
                logger.info(f"[queue] picked up {entity_type} {pid}")

                try:
                    if entity_type == 'company':
                        from companies.infrastructure.workers.company_worker import process_company
                        process_company(pid)
                    else:
                        from jobs.infrastructure.workers.worker import process_job
                        process_job(pid)
                except Exception as e:
                    logger.error(f"[queue] {entity_type} {pid} raised: {e}")

            except Exception as e:
                logger.error(f"[queue] Worker error: {e}")
                time.sleep(2)


_queue_manager: Optional[JobQueueManager] = None


def init_queue_manager(db_path: str) -> JobQueueManager:
    global _queue_manager
    _queue_manager = JobQueueManager()
    _queue_manager.start()
    return _queue_manager


def get_queue_manager() -> JobQueueManager:
    if _queue_manager is None:
        raise RuntimeError("Queue manager not initialized.")
    return _queue_manager
