# Prompt 198 - Truthful timeout message + configurable reconcile interval

## Objective

Two clarity fixes on top of #197:
1. The processing timeout/warning message always printed the static `WORKER_JOB_TIMEOUT`
   (600s) label regardless of real runtime. Make it report the **actual elapsed
   seconds** since `started_at` so the UI/ops text is truthful (e.g. "exceeded 612s").
2. The `reconcile_stuck_executions` sweep cadence was hardcoded to 30s. Expose it as
   `RECONCILE_INTERVAL_SECONDS` in `.env` so operators can tune the interval without a deploy.

## Current State

- `apps/backend/shared/infrastructure/taskiq/tasks.py:41` — `_build_timeout_message(heartbeat_at, timeout)`; callers pass `WORKER_JOB_TIMEOUT` (600) so text always says "600s".
- `apps/backend/shared/infrastructure/taskiq/tasks.py:93` — `@broker.task(schedule=[{"interval": 30}])` (hardcoded).
- `apps/backend/shared/infrastructure/taskiq/config.py:37` — `WORKER_JOB_TIMEOUT` env var (pattern to mirror).
- `apps/backend/.env:17` — `WORKER_JOB_TIMEOUT=600`.
- `apps/backend/shared/infrastructure/taskiq/tasks.py:143-202` — `reconcile_stuck_executions` computes the warning/timeout from `WORKER_JOB_TIMEOUT` (trigger threshold) but never the real elapsed.

## Changes

### Backend

1. **`config.py`** — add `RECONCILE_INTERVAL_SECONDS = int(os.environ.get("RECONCILE_INTERVAL_SECONDS", "30"))`.
2. **`tasks.py`**:
   - import `RECONCILE_INTERVAL_SECONDS`; use it in the reconcile schedule.
   - add helper `_elapsed_seconds(started_at) -> int` (returns 0 if `None`/bad).
   - in both the dead (`stale_running`) and long-running (`long_running`) branches, compute `elapsed = _elapsed_seconds(execution.started_at)` and pass `elapsed` (not `WORKER_JOB_TIMEOUT`) to `_build_timeout_message`. Keep `WORKER_JOB_TIMEOUT` as the query threshold.
   - add `elapsed_seconds=elapsed` to the `taskiq.task.reconcile.timeout` and `taskiq.task.reconcile.long_running` log lines.
3. **`.env`** — add `RECONCILE_INTERVAL_SECONDS=30`.

### Tests

- `test_tasks_timeout_message.py` — assert the **dynamic** value appears (e.g. 612 → "exceeded 612s"; 605 → "timed out after 605s"); add `test_elapsed_seconds_uses_real_start_time`.
- `test_reconcile_long_running.py` — seed `started_at` 612s ago; assert warning contains "exceeded 612s" and is non-terminal.
- `test_taskiq_config.py` (new) — default 30 and env override honored.

### Docs

- `docs/domain/processing/events.md` — note the message reports actual elapsed and the interval is env-configurable (`RECONCILE_INTERVAL_SECONDS`).

## Testing Requirements

- `uv run pytest apps/backend/tests/shared/infrastructure/taskiq/ -v` (all pass).
- `uv run ruff check apps/backend/shared/infrastructure/taskiq/tasks.py apps/backend/shared/infrastructure/taskiq/config.py` clean.

## Constraints

- No DB migration; interval + message are app/config only.
- `WORKER_JOB_TIMEOUT` stays the trigger threshold and remains env-configurable.
- Frontend 600s stalled-prompt threshold unchanged (out of scope; would need a settings endpoint to share the value).
- Keep `@broker.task` schedule readable from the env at import time.
