# Prompt 187 - Fix Processing Queue Concurrency

## Objective

Fix the issue where adding new jobs moves them to the queue without running the process. Only one process runs at a time, and after it completes, queued jobs never start. Ensure WORKER_CONCURRENCY from .env controls the number of concurrent processing jobs/companies.

## Current State

- `apps/backend/shared/infrastructure/taskiq/config.py:34` — `WORKER_CONCURRENCY` read from env (default 4)
- `apps/backend/entrypoints/worker.py:37` — passed as `WorkerArgs(workers=WORKER_CONCURRENCY)` to TaskIQ
- `apps/backend/shared/infrastructure/taskiq/tasks.py:51` — `process_execution_task` decorated with retry_on_error
- `apps/backend/processing/infrastructure/repositories/sa_processing_execution_repository.py:105` — `_ACTIVE_STATUSES = ("queued", "starting", "running", "failed")` includes "failed", blocking reprocessing
- `apps/backend/processing/application/use_cases/create_processing_execution.py:30` — checks `active_execution()` which uses `_ACTIVE_STATUSES`, raising ConflictError if any active execution exists (including failed)
- `apps/backend/shared/infrastructure/taskiq/client.py:41` — `enqueue_execution_sync` creates short-lived broker per enqueue call
- No reconciliation mechanism for stuck QUEUED/RUNNING executions

## Changes

1. **`apps/backend/processing/application/use_cases/create_processing_execution.py`** — Auto-cancel failed active executions before creating new ones (same logic as `ExecutionActionService.reprocess()`)

2. **`apps/backend/shared/infrastructure/taskiq/tasks.py`** — Add `reconcile_stuck_executions` periodic task that:
   - Re-enqueues QUEUED executions stuck > 60s
   - Fails RUNNING executions stuck > WORKER_JOB_TIMEOUT (600s)

3. **`apps/backend/entrypoints/scheduler.py`** — Register the new reconcile task

4. **`apps/backend/entrypoints/worker.py`** — Add `load_dotenv()` at top, log WORKER_CONCURRENCY at startup

5. **`apps/backend/processing/infrastructure/repositories/sa_processing_execution_repository.py`** — Add `stale_queued_executions()` and `stale_running_executions()` query methods

## Testing Requirements

- `uv run pytest apps/backend/tests/ -v` (backend tests)
- Manual: add 5+ jobs with queue=true, verify all process concurrently up to WORKER_CONCURRENCY

## Constraints

- Respect AGENTS.md rules: no cross-context FKs, DDD boundaries, structlog logging
- No new API routes in entrypoints/api.py
- EDD: domain events documented but pub/sub deferred
