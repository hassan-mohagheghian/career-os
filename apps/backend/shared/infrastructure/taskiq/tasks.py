"""TaskIQ task definitions.

These tasks are thin infrastructure wrappers that coordinate background
execution. They do NOT contain business logic — they delegate to the existing
application services / workers which own the LangGraph workflow execution.

Each task mirrors the previous ARQ task it replaces:

- process_execution_task → drives the ProcessingExecution lifecycle through
  the TaskIQ worker → LangGraph workflow flow.
- periodic_db_backup     → scheduled PostgreSQL backup during dev (see
  ``DB_BACKUP_INTERVAL_MINUTES`` / ``DB_BACKUP_KEEP_COUNT`` in .env).
"""

from __future__ import annotations

import asyncio

from shared.infrastructure.config.app_config import DB_BACKUP_INTERVAL_MINUTES
from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.taskiq.config import (
    broker,
    WORKER_MAX_RETRIES,
    WORKER_RETRY_BACKOFF,
)

log = get_logger("taskiq.tasks")


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


@broker.task(retry_on_error=True, retry_count=WORKER_MAX_RETRIES, retry_delay=WORKER_RETRY_BACKOFF)
async def process_execution_task(execution_id: str) -> dict:
    """Run a ProcessingExecution through its LangGraph workflow.

    Flow:
    - Load ProcessingExecution
    - Mark execution running
    - Start LangGraph workflow for the execution's target
    - Complete or fail the execution
    """
    log.info("taskiq.task.execution.start", execution_id=execution_id)
    try:
        from processing.infrastructure.runner.execution_runner import ProcessingExecutionRunner

        runner = ProcessingExecutionRunner()
        result = await asyncio.to_thread(runner.run, execution_id)
        log.info("taskiq.task.execution.complete", execution_id=execution_id)
        return {"status": "completed", "execution_id": execution_id, **result}
    except Exception as e:
        log.error("taskiq.task.execution.failed", execution_id=execution_id, error=str(e))
        raise
