# Prompt 188 - Fix Reconcile False Positive: Add Worker Heartbeat

## Objective

Fix the race condition where `reconcile_stuck_executions` prematurely marks RUNNING executions as FAILED with "Execution timed out after 600s (worker crash suspected)" while the worker thread is still actively processing. The LLM analysis steps (Analyze Job/Company/Candidate) routinely exceed the 600s timeout. The processes complete successfully, but the user sees a transient FAILED state. Root cause: reconcile has no way to know if a worker is still alive.

## Current State

- `apps/backend/shared/infrastructure/taskiq/config.py:37` — `WORKER_JOB_TIMEOUT=600` (from .env)
- `apps/backend/shared/infrastructure/taskiq/tasks.py:57-141` — `reconcile_stuck_executions` runs every 30s, marks RUNNING executions as FAILED when `started_at` is older than `WORKER_JOB_TIMEOUT`
- `apps/backend/shared/infrastructure/taskiq/tasks.py:149-182` — `process_execution_task` wraps `runner.run()` in `asyncio.wait_for(asyncio.to_thread(...), timeout=WORKER_JOB_TIMEOUT + 60)`. **Critical bug**: `asyncio.to_thread` does NOT cancel the underlying thread when the future times out. The thread continues running, but TaskIQ considers the task failed.
- `apps/backend/processing/infrastructure/runner/execution_runner.py:93-173` — `ProcessingExecutionRunner.run()` marks execution RUNNING at start, COMPLETED/FAILED at end. No heartbeat during long LLM calls.
- `apps/backend/processing/infrastructure/models/processing_execution_model.py` — No `heartbeat_at` column
- `apps/backend/processing/domain/entities/processing_execution.py` — No `heartbeat_at` field
- `apps/backend/processing/infrastructure/repositories/sa_processing_execution_repository.py:274-290` — `stale_running_executions()` checks only `started_at < cutoff`

## Changes

### 1. Domain entity — add `heartbeat_at`

**`apps/backend/processing/domain/entities/processing_execution.py`**
- Add `heartbeat_at: datetime | None = None` parameter to `__init__`
- Add `heartbeat_at` property with getter/setter
- Include in `to_dict()` and `from_dict()`

### 2. DB model — add `heartbeat_at` column

**`apps/backend/processing/infrastructure/models/processing_execution_model.py`**
- Add `heartbeat_at: Mapped[Optional[datetime]] = mapped_column(Text, nullable=True)`

### 3. Alembic migration

- Add `apps/alembic/processing/versions` to `version_locations` in `alembic.ini`
- Create `apps/alembic/processing/versions/processing_001_add_heartbeat_at.py` with branch label `processing`
- Run `uv run alembic upgrade head` to apply

### 4. Repository — update save/load and stale query

**`apps/backend/processing/infrastructure/repositories/sa_processing_execution_repository.py`**
- `save()`: include `heartbeat_at` in model update and new model creation
- `model_to_dict()`: include `heartbeat_at`
- `stale_running_executions()`: check `heartbeat_at` instead of `started_at`. An execution is stale only if `heartbeat_at` is not None AND `heartbeat_at < cutoff` (heartbeat older than `WORKER_JOB_TIMEOUT` seconds). Fall back to `started_at` when `heartbeat_at` is None (legacy rows).

### 5. Runner — add heartbeat thread

**`apps/backend/processing/infrastructure/runner/execution_runner.py`**
- In `run()`, after marking execution RUNNING, start a daemon thread that updates `heartbeat_at` every 30 seconds via `repo.save()`
- On completion/failure/exception, signal the heartbeat thread to stop and join it
- Use `threading.Event` for clean shutdown

### 6. TaskIQ task — remove broken `asyncio.wait_for` timeout

**`apps/backend/shared/infrastructure/taskiq/tasks.py`**
- In `process_execution_task`: remove `asyncio.wait_for(..., timeout=...)`. Call `await asyncio.to_thread(runner.run, execution_id)` directly. The reconcile task now handles crash detection via heartbeat.
- Remove the `TimeoutError` exception handler (no longer needed)
- Keep `WORKER_MAX_RETRIES` and `WORKER_RETRY_BACKOFF` for transient errors

### 7. Reconcile task — use heartbeat for staleness check

**`apps/backend/shared/infrastructure/taskiq/tasks.py`**
- No change needed to the reconcile task logic itself — it already calls `stale_running_executions(WORKER_JOB_TIMEOUT)` which will now use heartbeat-based detection after change #4

## Testing Requirements

- `uv run pytest apps/backend/tests/processing/ -v`
- `uv run pytest apps/backend/tests/ -v` (full suite)
- Verify reconcile query correctly distinguishes active vs dead workers:
  - Execution with fresh heartbeat (<600s) → NOT stale
  - Execution with stale heartbeat (>600s) → stale
  - Execution with NULL heartbeat and old started_at → stale (legacy)

## Constraints

- Respect AGENTS.md rules: no cross-context FKs, DDD boundaries, structlog logging
- Heartbeat thread must be daemon + use clean shutdown via Event to avoid hanging on worker shutdown
- Heartbeat DB writes must be best-effort (catch exceptions, never crash the runner)
- Keep backward compatibility: legacy executions without `heartbeat_at` must still be caught by reconcile using `started_at`
