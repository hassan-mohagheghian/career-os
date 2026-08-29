# Prompt 199 - Never fail an alive (fresh-heartbeat) worker

## Objective

Fix a bug where a RUNNING execution whose worker is still heartbeating could be
moved to a `FAILED`/error state with the message "Execution exceeded <n>s but the
worker is still reporting progress". An execution that is still reporting progress
(alive) must never be failed — only truly-dead workers (stale heartbeat) should be.

## Current State

- `apps/backend/shared/infrastructure/taskiq/tasks.py:150` — `reconcile_stuck_executions`
  fails every execution returned by `stale_running_executions(HEARTBEAT_RECENT_WINDOW_SECONDS * 2)`
  and then calls `_build_timeout_message(heartbeat_at, elapsed)`. That helper prints
  "still reporting progress" whenever it parses `heartbeat_at` as recent (< 90s).
- `stale_running_executions` (`sa_processing_execution_repository.py:277`) compares
  `heartbeat_at < cutoff` on a **`Text` column** (`processing_execution_model.py`
  stores `heartbeat_at` as `Text`). Lexicographic comparison of ISO timestamps can
  misclassify a fresh heartbeat as stale, so a 22s-old alive worker can be selected
  as "stale", failed, and then the helper prints "still reporting progress" because
  in Python the heartbeat parses as fresh. Result: alive worker → FAILED.
- The non-terminal warning path (`long_running_executions`) never fails, but it is
  only reached for `started_at > 600s`; a freshly-started alive worker misclassified
  by the stale query still gets failed.

## Changes

### Backend (`tasks.py`)

1. Add `_is_heartbeat_recent(heartbeat_at) -> bool` — Python-side freshness check
   (`(now - heartbeat_at) < HEARTBEAT_RECENT_WINDOW_SECONDS`), tolerating `None`/bad
   values (returns `False`).
2. In the `stale_running` loop, before failing, compute `recent = _is_heartbeat_recent(...)`.
   - If `recent` → the worker is alive: set `workflow_progress["warning"]`
     (`_build_timeout_message(heartbeat_at, elapsed)`), publish `EXECUTION_WARNING`,
     increment `warned`, and `continue` (do NOT fail).
   - Else → genuinely dead: fail with `EXECUTION_FAILED` as before.
3. Move `warned = 0` initialization above the `stale_running` loop (it is now
   incremented there too).

### Tests

`apps/backend/tests/shared/infrastructure/taskiq/test_reconcile_long_running.py`:
- `test_reconcile_does_not_fail_alive_fresh_heartbeat`: `stale_running` returns a
  22s-old, fresh-heartbeat (20s) execution → NOT failed, `EXECUTION_WARNING` emitted,
  `EXECUTION_FAILED` not emitted.
- `test_reconcile_fails_truly_dead_stale_heartbeat`: `stale_running` returns a
  400s-stale-heartbeat execution → failed with "worker stopped responding",
  `EXECUTION_FAILED` emitted.
- (Existing `test_reconcile_warns_long_running_not_fails` still covers the long_running branch.)

### Docs

- `docs/domain/processing/events.md` — note alive workers are never failed; only
  genuinely-dead workers get `EXECUTION_FAILED`; the `Text`-column comparison caveat.

## Testing Requirements

- `uv run pytest apps/backend/tests/shared/infrastructure/taskiq/ -v` (all pass).
- `uv run ruff check apps/backend/shared/infrastructure/taskiq/tasks.py` clean.

## Constraints

- No DB migration (the Python-side freshness gate avoids relying on the `Text`
  column comparison; a future hardening could store `heartbeat_at`/`started_at` as
  `TIMESTAMP` columns, but it is not required to fix the bug).
- Keep crash recovery: a truly-dead worker (stale heartbeat) is still failed.
- Best-effort event publishing; warning must never change business behavior.
