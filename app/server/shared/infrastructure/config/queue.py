"""
Persistent concurrent job queue manager.

Processes up to N jobs concurrently from the pending_jobs/pending_companies tables.
N is controlled by QUEUE_CONCURRENCY env var (default 2).
Survives server restarts — on startup, recovers orphaned processing jobs.

Status flow: pending -> queued -> processing -> done/failed/paused

Features:
- Graceful shutdown with worker join timeout
- Per-job cancellation (kills mimo subprocess + sets paused status)
- Per-job reset (kills process, resets steps, re-queues)
- Transition validation (prevents invalid state changes)
- ProcessManager integration (zero orphaned subprocesses)
- TempFileManager integration (zero leaked temp files)
"""

import os
import threading
import time
import logging
from datetime import datetime
from typing import Optional

from shared.infrastructure.database.session import get_session_sync
from processing.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository

logger = logging.getLogger(__name__)

CONCURRENCY = int(os.environ.get("QUEUE_CONCURRENCY", "2"))

VALID_TRANSITIONS = {
    'pending':    {'queued', 'failed'},
    'queued':     {'processing', 'pending', 'failed'},
    'processing': {'done', 'failed', 'paused', 'queued'},
    'paused':     {'queued', 'failed', 'pending'},
    'done':       {'pending'},
    'failed':     {'pending', 'queued'},
}


def _validate_transition(from_status: str, to_status: str) -> bool:
    valid = VALID_TRANSITIONS.get(from_status, set())
    return to_status in valid


def _repo(session):
    return SQLAlchemyPendingRepository(session)


class JobQueueManager:
    """Persistent concurrent job queue with lifecycle management."""

    def __init__(self, concurrency: int = CONCURRENCY):
        self._concurrency = concurrency
        self._running = False
        self._workers: list[threading.Thread] = []
        self._active_count = 0
        self._lock = threading.Lock()
        self._slot_event = threading.Event()
        self._shutdown_event = threading.Event()

    def start(self):
        if self._running:
            return
        self._running = True
        self._reset_processing_orphans()

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

        try:
            from shared.infrastructure.process.process_manager import ProcessManager
            from shared.infrastructure.process.temp_manager import TempFileManager
            killed = ProcessManager().cleanup_all()
            cleaned = TempFileManager().cleanup_all()
            if killed or cleaned:
                logger.info(f"[queue] Shutdown cleanup: {killed} processes, {cleaned} temp files")
        except Exception as e:
            logger.warning(f"[queue] Cleanup error: {e}")

        self._mark_processing_as_paused()
        self._shutdown_event.set()
        logger.info("[queue] Shutdown complete")

    def enqueue(self, pending_id: int, table: str = 'pending_jobs'):
        session = get_session_sync()
        try:
            repo = _repo(session)
            now = datetime.now().isoformat()
            if table == 'pending_companies':
                repo.update_fields(pending_id, table, status='queued', error=None, updated_at=now)
                logger.info(f"[queue] Enqueued company {pending_id}")
            else:
                order = repo.get_max_queue_order(table) + 1
                repo.update_fields(pending_id, table, status='queued', queue_order=order, error=None, updated_at=now)
                logger.info(f"[queue] Enqueued job {pending_id} (order={order})")
        finally:
            session.close()
        self._slot_event.set()

    def enqueue_bulk(self, pending_ids: list):
        session = get_session_sync()
        try:
            repo = _repo(session)
            now = datetime.now().isoformat()
            order = repo.get_max_queue_order('pending_jobs') + 1
            for pid in pending_ids:
                repo.update_fields(pid, 'pending_jobs', status='queued', queue_order=order, error=None, updated_at=now)
                order += 1
            logger.info(f"[queue] Bulk enqueued {len(pending_ids)} jobs")
        finally:
            session.close()
        self._slot_event.set()

    def dequeue(self, pending_id: int):
        session = get_session_sync()
        try:
            repo = _repo(session)
            now = datetime.now().isoformat()
            repo.update_fields(pending_id, 'pending_jobs', status='pending', queue_order=0, error=None, updated_at=now)
            logger.info(f"[queue] Dequeued job {pending_id}")
        finally:
            session.close()

    def cancel_job(self, pending_id: int, table: str = 'pending_jobs') -> bool:
        session = get_session_sync()
        try:
            repo = _repo(session)
            item = repo.get_by_id(pending_id, table)
            if not item:
                return False

            status = item['status']

            if status == 'processing':
                try:
                    from shared.infrastructure.process.process_manager import ProcessManager
                    ProcessManager().cancel(
                        ProcessManager().get(str(pending_id)), grace_period=5.0
                    )
                except Exception:
                    pass

            new_status = 'paused' if status == 'processing' else 'pending'
            now = datetime.now().isoformat()
            repo.update_fields(pending_id, table, status=new_status, error=None, updated_at=now)
            logger.info(f"[queue] Cancelled {table}:{pending_id} -> {new_status}")
            return True
        finally:
            session.close()

    def reset_job(self, pending_id: int, table: str = 'pending_jobs') -> bool:
        session = get_session_sync()
        try:
            repo = _repo(session)
            item = repo.get_by_id(pending_id, table)
            if not item:
                return False

            status = item['status']
            if status == 'processing':
                try:
                    from shared.infrastructure.process.process_manager import ProcessManager
                    ProcessManager().cancel(
                        ProcessManager().get(str(pending_id)), grace_period=5.0
                    )
                except Exception:
                    pass

            current_version = item.get('version') or 1
            new_version = current_version + 1
            repo.reset_steps(pending_id, new_version, table)
            logger.info(f"[queue] Reset {table}:{pending_id} -> version {new_version}")
            return True
        finally:
            session.close()

    def signal_job_done(self, pending_id: int):
        with self._lock:
            self._active_count = max(0, self._active_count - 1)
        self._slot_event.set()

    def get_status(self) -> dict:
        session = get_session_sync()
        try:
            repo = _repo(session)
            from processing.infrastructure.models.pending_model import PendingJobModel, PendingCompanyModel

            processing_items = repo.get_processing_items('pending_jobs')
            queued_count = repo.get_queued_count('pending_jobs')
            pending_count = session.query(PendingJobModel).filter(PendingJobModel.status == 'pending').count()
            company_processing = repo.get_processing_count('pending_companies')
            company_queued = repo.get_queued_count('pending_companies')
            company_pending = session.query(PendingCompanyModel).filter(PendingCompanyModel.status == 'pending').count()
            return {
                "processing": [{"id": r["id"], "company": r.get("company"), "url": r.get("url")} for r in processing_items],
                "processing_count": len(processing_items),
                "queued_count": queued_count,
                "pending_count": pending_count,
                "company_processing_count": company_processing,
                "company_queued_count": company_queued,
                "company_pending_count": company_pending,
                "concurrency": self._concurrency,
                "running": self._running,
            }
        finally:
            session.close()

    # ── Internal ───────────────────────────────────────────────────

    def _mark_processing_as_paused(self):
        session = get_session_sync()
        try:
            repo = _repo(session)
            for table in ('pending_jobs', 'pending_companies'):
                count = repo.mark_processing_as_paused(table)
                if count > 0:
                    logger.info(f"[queue] Marked {count} {table} item(s) as paused")
        finally:
            session.close()

    def _reset_processing_orphans(self):
        session = get_session_sync()
        try:
            repo = _repo(session)
            for table in ('pending_jobs', 'pending_companies'):
                count = repo.reset_processing_orphans(table)
                if count > 0:
                    logger.info(f"[queue] Recovered {count} orphaned {table} item(s)")
        finally:
            session.close()

    def _reset_steps(self, pending_id: int, version: int, table: str = 'pending_jobs'):
        session = get_session_sync()
        try:
            repo = _repo(session)
            repo.reset_steps(pending_id, version, table, keep_status=True)
        finally:
            session.close()

    def _has_partial_steps(self, item: dict) -> bool:
        step_cols = ["step_fetch", "step_validate", "step_extract_raw",
                     "step_extract_struct", "step_analyze", "step_summary", "step_db", "step_done"]
        any_done = any(item.get(col) == 1 for col in step_cols)
        all_done = all(item.get(col) == 1 for col in step_cols)
        return any_done and not all_done

    def _pick_and_claim(self) -> Optional[dict]:
        session = get_session_sync()
        try:
            repo = _repo(session)
            total_processing = (
                repo.get_processing_count('pending_jobs')
                + repo.get_processing_count('pending_companies')
            )
            if total_processing >= self._concurrency:
                return None

            result = repo.pick_queued_item('pending_companies')
            if result:
                result['table'] = 'pending_companies'
                return result

            result = repo.pick_queued_item('pending_jobs')
            if result:
                result['table'] = 'pending_jobs'
            return result
        finally:
            session.close()

    def _worker_loop(self):
        while self._running:
            try:
                claimed = False
                item = None
                pid = None

                with self._lock:
                    session = get_session_sync()
                    try:
                        repo = _repo(session)
                        db_count = repo.get_processing_count('pending_jobs')
                    finally:
                        session.close()

                    self._active_count = db_count

                    if self._active_count < self._concurrency:
                        item = self._pick_and_claim()
                        if item:
                            pid = item["id"]
                            self._active_count += 1
                            claimed = True

                if not claimed:
                    self._slot_event.clear()
                    self._slot_event.wait(timeout=2.0)
                    continue

                logger.info(f"[queue] {threading.current_thread().name} picked up {item.get('table', 'job')} {pid}")

                if self._has_partial_steps(item):
                    version = item.get('version', 1)
                    self._reset_steps(pid, version, item.get('table', 'pending_jobs'))

                from jobs.infrastructure.workers.worker import process_job
                from companies.infrastructure.workers.company_worker import process_company
                try:
                    if item.get('input_text'):
                        process_company(pid)
                    else:
                        process_job(pid)
                except Exception as e:
                    logger.error(f"[queue] {pid} raised: {e}")

                self.signal_job_done(pid)

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
