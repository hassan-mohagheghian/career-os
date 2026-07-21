"""
Persistent concurrent job queue manager.

Processes up to N jobs concurrently from the pending_jobs table.
N is controlled by QUEUE_CONCURRENCY env var (default 2).
Survives server restarts — on startup, recovers orphaned processing jobs
and resumes the queue from the last point.

Status flow: pending → queued → processing → done/failed
"""

import os
import sqlite3
import threading
import time
import logging
from datetime import datetime
from typing import Optional

DB_PATH = None  # Set by init_queue_manager()

logger = logging.getLogger(__name__)

CONCURRENCY = int(os.environ.get("QUEUE_CONCURRENCY", "2"))


def _db():
    """Open a fresh DB connection with WAL mode and retry on lock."""
    for attempt in range(5):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            return conn
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < 4:
                time.sleep(0.5 * (attempt + 1))
            else:
                raise


class JobQueueManager:
    """Persistent concurrent job queue. Processes up to N jobs at a time."""

    def __init__(self, concurrency: int = CONCURRENCY):
        self._concurrency = concurrency
        self._running = False
        self._workers: list[threading.Thread] = []
        self._active_count = 0
        self._lock = threading.Lock()
        self._slot_event = threading.Event()  # signaled when a worker finishes

    def start(self):
        """Start the queue processor workers."""
        if self._running:
            return
        self._running = True
        self._reset_processing_orphans()

        for i in range(self._concurrency):
            t = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name=f"job-queue-{i}",
            )
            self._workers.append(t)
            t.start()

        logger.info(f"[queue] Queue manager started with {self._concurrency} workers")

    def stop(self):
        """Stop all workers."""
        self._running = False
        self._slot_event.set()  # wake all workers so they can exit

    def enqueue(self, pending_id: int):
        """Move a pending job to queued status with the next queue_order."""
        conn = _db()
        try:
            row = conn.execute(
                "SELECT MAX(queue_order) as max_q FROM pending_jobs WHERE status='queued'"
            ).fetchone()
            next_order = (dict(row)["max_q"] or 0) + 1

            conn.execute(
                """UPDATE pending_jobs SET status='queued', queue_order=?, error=NULL,
                   updated_at=? WHERE id=?""",
                (next_order, datetime.now().isoformat(), pending_id),
            )
            conn.commit()
            logger.info(f"[queue] Enqueued job {pending_id} (order={next_order})")
        finally:
            conn.close()

        self._slot_event.set()

    def enqueue_bulk(self, pending_ids: list):
        """Move multiple pending jobs to queued, preserving insertion order."""
        conn = _db()
        try:
            row = conn.execute(
                "SELECT MAX(queue_order) as max_q FROM pending_jobs WHERE status='queued'"
            ).fetchone()
            next_order = (dict(row)["max_q"] or 0) + 1

            for pid in pending_ids:
                conn.execute(
                    """UPDATE pending_jobs SET status='queued', queue_order=?, error=NULL,
                       updated_at=? WHERE id=?""",
                    (next_order, datetime.now().isoformat(), pid),
                )
                next_order += 1

            conn.commit()
            logger.info(
                f"[queue] Bulk enqueued {len(pending_ids)} jobs "
                f"(orders {next_order - len(pending_ids)}-{next_order - 1})"
            )
        finally:
            conn.close()

        self._slot_event.set()

    def dequeue(self, pending_id: int):
        """Move a queued job back to pending status."""
        conn = _db()
        try:
            conn.execute(
                """UPDATE pending_jobs SET status='pending', queue_order=0, error=NULL,
                   updated_at=? WHERE id=?""",
                (datetime.now().isoformat(), pending_id),
            )
            conn.commit()
            logger.info(f"[queue] Dequeued job {pending_id}")
        finally:
            conn.close()

    def signal_job_done(self, pending_id: int):
        """Called by worker when a job finishes. Wakes up idle workers."""
        with self._lock:
            self._active_count = max(0, self._active_count - 1)
        self._slot_event.set()

    def get_status(self) -> dict:
        """Return current queue status for the API."""
        conn = _db()
        try:
            processing_rows = conn.execute(
                "SELECT id, company, url FROM pending_jobs WHERE status='processing'"
            ).fetchall()
            queued_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM pending_jobs WHERE status='queued'"
            ).fetchone()["cnt"]
            pending_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM pending_jobs WHERE status='pending'"
            ).fetchone()["cnt"]
            return {
                "processing": [dict(r) for r in processing_rows],
                "processing_count": len(processing_rows),
                "queued_count": queued_count,
                "pending_count": pending_count,
                "concurrency": self._concurrency,
                "running": self._running,
            }
        finally:
            conn.close()

    # ── Internal methods ──────────────────────────────────────────

    def _reset_processing_orphans(self):
        """On startup: reset any orphaned 'processing' jobs to 'queued'."""
        conn = _db()
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM pending_jobs WHERE status='processing'"
            ).fetchone()
            count = row["cnt"]
            if count > 0:
                max_row = conn.execute(
                    "SELECT MAX(queue_order) as max_q FROM pending_jobs WHERE status='queued'"
                ).fetchone()
                next_order = (dict(max_row)["max_q"] or 0) + 1

                conn.execute(
                    """UPDATE pending_jobs SET status='queued', queue_order=?, error=NULL,
                       updated_at=? WHERE status='processing'""",
                    (next_order, datetime.now().isoformat()),
                )
                conn.commit()
                logger.info(f"[queue] Recovered {count} orphaned processing job(s) → queued")
        finally:
            conn.close()

    def _reset_steps(self, pending_id: int):
        """Reset all pipeline steps to 0 so the job starts from scratch."""
        conn = _db()
        try:
            conn.execute(
                """UPDATE pending_jobs SET
                   step_fetch=0, step_validate=0, step_extract_raw=0,
                   step_extract_struct=0, step_analyze=0, step_summary=0,
                   step_db=0, step_done=0, workflow_log='[]',
                   updated_at=? WHERE id=?""",
                (datetime.now().isoformat(), pending_id),
            )
            conn.commit()
            logger.info(f"[queue] Reset steps for job {pending_id}")
        finally:
            conn.close()

    def _has_partial_steps(self, item: dict) -> bool:
        """Check if a job has any partially-completed steps (needs reset)."""
        step_cols = [
            "step_fetch", "step_validate", "step_extract_raw",
            "step_extract_struct", "step_analyze", "step_summary",
            "step_db", "step_done",
        ]
        any_done = any(item.get(col) == 1 for col in step_cols)
        all_done = all(item.get(col) == 1 for col in step_cols)
        return any_done and not all_done

    def _pick_and_claim(self) -> Optional[dict]:
        """Atomically pick the next queued job and mark it as processing.

        Uses a DB-level atomic update to prevent two workers from
        grabbing the same job.
        """
        conn = _db()
        try:
            # Find the next queued job
            row = conn.execute(
                """SELECT id FROM pending_jobs WHERE status='queued'
                   ORDER BY queue_order ASC, created_at ASC LIMIT 1"""
            ).fetchone()
            if not row:
                return None

            pid = dict(row)["id"]

            # Atomically claim it — only succeeds if still queued
            updated = conn.execute(
                """UPDATE pending_jobs SET status='processing', updated_at=?
                   WHERE id=? AND status='queued'""",
                (datetime.now().isoformat(), pid),
            ).rowcount
            conn.commit()

            if updated == 0:
                # Another worker already claimed it
                return None

            # Re-read the full row
            row = conn.execute("SELECT * FROM pending_jobs WHERE id=?", (pid,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def _worker_loop(self):
        """Worker thread: pick claimed job, process it, repeat."""
        while self._running:
            try:
                # Check if we have a free slot
                with self._lock:
                    if self._active_count >= self._concurrency:
                        # All slots full — wait
                        self._slot_event.clear()
                        self._slot_event.wait(timeout=2.0)
                        continue

                item = self._pick_and_claim()
                if not item:
                    # No queued jobs — wait for enqueue signal
                    self._slot_event.clear()
                    self._slot_event.wait(timeout=2.0)
                    continue

                pid = item["id"]

                with self._lock:
                    self._active_count += 1

                logger.info(
                    f"[queue] Worker {threading.current_thread().name} "
                    f"picked up job {pid} ({item.get('company', 'unknown')})"
                )

                # Reset steps if job has partial progress (broken workflow)
                if self._has_partial_steps(item):
                    logger.info(f"[queue] Job {pid} has partial steps — resetting")
                    self._reset_steps(pid)

                # Run the pipeline (blocking call)
                from services.worker import process_job
                try:
                    process_job(pid)
                except Exception as e:
                    logger.error(f"[queue] Job {pid} raised exception: {e}")

                # Signal done — frees a slot
                self.signal_job_done(pid)

            except Exception as e:
                logger.error(f"[queue] Worker error: {e}")
                time.sleep(2)


# Singleton instance
_queue_manager: Optional[JobQueueManager] = None


def init_queue_manager(db_path: str) -> JobQueueManager:
    """Initialize and start the queue manager. Call once at app startup."""
    global _queue_manager, DB_PATH
    DB_PATH = db_path
    _queue_manager = JobQueueManager()
    _queue_manager.start()
    return _queue_manager


def get_queue_manager() -> JobQueueManager:
    """Get the singleton queue manager instance."""
    if _queue_manager is None:
        raise RuntimeError("Queue manager not initialized. Call init_queue_manager() first.")
    return _queue_manager
