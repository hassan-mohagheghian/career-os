"""TaskIQ task definitions.

These tasks are thin infrastructure wrappers that coordinate background
execution. They do NOT contain business logic — they delegate to the existing
application services / workers which own the LangGraph workflow execution.

Each task mirrors the previous ARQ task it replaces:

- process_execution_task → drives the ProcessingExecution lifecycle through
  the TaskIQ worker → LangGraph workflow flow.
- reconcile_stuck_executions → periodic sweep that re-enqueues stuck QUEUED
  executions and fails stale RUNNING executions (worker crash recovery).
- periodic_db_backup     → scheduled PostgreSQL backup during dev (see
  ``DB_BACKUP_INTERVAL_MINUTES`` / ``DB_BACKUP_KEEP_COUNT`` in .env).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, UTC
from typing import Optional

from shared.infrastructure.config.app_config import DB_BACKUP_INTERVAL_MINUTES
from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.taskiq.config import (
    broker,
    WORKER_MAX_RETRIES,
    WORKER_RETRY_BACKOFF,
    WORKER_JOB_TIMEOUT,
    RECONCILE_INTERVAL_SECONDS,
)

log = get_logger("taskiq.tasks")


def _elapsed_seconds(started_at: Optional[datetime]) -> int:
    """Real wall-clock seconds since the execution started (0 if unknown)."""
    if started_at is None:
        return 0
    try:
        delta = (datetime.now(UTC) - started_at).total_seconds()
    except TypeError:
        return 0
    return int(max(0, delta))


def _timeout_message(elapsed: int) -> str:
    """Plain, honest timeout message (no worker-liveness claim)."""
    return f"Execution timed out after {elapsed}s. Check status or retry."


@broker.task(
    schedule=[{"interval": int(DB_BACKUP_INTERVAL_MINUTES * 60)}],
)
async def periodic_db_backup() -> dict:
    """Backup the main database and prune old backups.

    Runs on a fixed interval (see ``DB_BACKUP_INTERVAL_MINUTES`` in .env) and
    keeps only the ``DB_BACKUP_KEEP_COUNT`` most recent dumps.
    """
    log.info("taskiq.task.db_backup.start")
    try:
        from shared.infrastructure.database.backup_service import run_db_backup

        result = await asyncio.to_thread(run_db_backup)
        log.info("taskiq.task.db_backup.complete", **result)
        return {"status": "completed", **result}
    except Exception as e:
        log.error("taskiq.task.db_backup.failed", error=str(e))
        raise


STALE_QUEUED_THRESHOLD_SECONDS = 60


@broker.task(
    schedule=[{"interval": RECONCILE_INTERVAL_SECONDS}],
)
async def reconcile_stuck_executions() -> dict:
    """Periodic sweep to recover stuck executions.

    - Re-enqueues QUEUED executions stuck for > 60s (likely lost from the
      Redis Stream after a worker crash or restart).
    - Fails RUNNING executions stuck for > WORKER_JOB_TIMEOUT seconds
      (worker process died mid-execution).
    """
    log.info("taskiq.task.reconcile.start")
    try:
        from shared.infrastructure.database.session import get_session_sync
        from processing.infrastructure.repositories.sa_processing_execution_repository import (
            SQLAlchemyProcessingExecutionRepository,
        )
        from processing.domain.enums import ExecutionStatus
        from shared.infrastructure.events import processing_events

        session = get_session_sync()
        try:
            repo = SQLAlchemyProcessingExecutionRepository(session)

            reenqueued = 0
            stale_queued = repo.stale_queued_executions(STALE_QUEUED_THRESHOLD_SECONDS)
            for execution in stale_queued:
                log.info(
                    "taskiq.task.reconcile.reenqueue",
                    execution_id=execution.id,
                    target_type=execution.target_type,
                    target_id=execution.target_id,
                )
                try:
                    from shared.infrastructure.taskiq.client import enqueue_execution

                    await enqueue_execution(execution.id)
                    reenqueued += 1
                except Exception as e:
                    log.error(
                        "taskiq.task.reconcile.reenqueue_failed",
                        execution_id=execution.id,
                        error=str(e),
                    )

            timed_out = 0
            stale_running = repo.stale_running_executions(WORKER_JOB_TIMEOUT)
            for execution in stale_running:
                elapsed = _elapsed_seconds(execution.started_at)
                log.info(
                    "taskiq.task.reconcile.timeout",
                    execution_id=execution.id,
                    target_type=execution.target_type,
                    target_id=execution.target_id,
                    elapsed_seconds=elapsed,
                )
                execution.status = ExecutionStatus.FAILED
                execution.finished_at = datetime.now(UTC)
                execution.error_message = _timeout_message(elapsed)
                if execution.workflow_progress:
                    execution.workflow_progress["status"] = "failed"
                repo.save(execution)
                await processing_events.publish(
                    processing_events.EXECUTION_FAILED,
                    execution.id,
                    execution.target_id if execution.target_type == "job" else None,
                    ExecutionStatus.FAILED.value,
                    message=execution.error_message,
                    target_type=execution.target_type,
                    target_id=execution.target_id,
                    updated_at=execution.finished_at.isoformat(),
                )
                timed_out += 1
        finally:
            session.close()

        log.info(
            "taskiq.task.reconcile.complete",
            reenqueued=reenqueued,
            timed_out=timed_out,
        )
        return {"status": "completed", "reenqueued": reenqueued, "timed_out": timed_out}
    except Exception as e:
        log.error("taskiq.task.reconcile.failed", error=str(e))
        raise


@broker.task(
    retry_on_error=True,
    retry_count=WORKER_MAX_RETRIES,
    retry_delay=WORKER_RETRY_BACKOFF,
)
async def process_execution_task(execution_id: str) -> dict:
    """Run a ProcessingExecution through its LangGraph workflow.

    Flow:
    - Load ProcessingExecution
    - Mark execution running
    - Start LangGraph workflow for the execution's target
    - Complete or fail the execution

    Crash detection is handled by ``reconcile_stuck_executions`` which fails
    any RUNNING execution that has exceeded ``WORKER_JOB_TIMEOUT``
    (wall-clock budget since ``started_at``).
    """
    log.info("taskiq.task.execution.start", execution_id=execution_id)
    try:
        from processing.infrastructure.runner.execution_runner import (
            ProcessingExecutionRunner,
        )

        runner = ProcessingExecutionRunner()
        result = await asyncio.to_thread(runner.run, execution_id)
        log.info("taskiq.task.execution.complete", execution_id=execution_id)
        return {"status": "completed", "execution_id": execution_id, **result}
    except Exception as e:
        log.error(
            "taskiq.task.execution.failed", execution_id=execution_id, error=str(e)
        )
        raise
