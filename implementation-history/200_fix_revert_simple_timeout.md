# Prompt 200 - Revert to simple 600s timeout failure

## Objective
Remove the alive/stale-heartbeat warning machinery (#197/#198/#199) and restore the
simple rule: a RUNNING execution older than `WORKER_JOB_TIMEOUT` (600s) is moved to
FAILED. No heartbeat liveness checks, no warning path, no frontend warning UI.

## Current State
- `shared/infrastructure/taskiq/tasks.py` had `HEARTBEAT_RECENT_WINDOW_SECONDS`,
  `_is_heartbeat_recent`, `_build_timeout_message` (emits "still reporting progress"
  for fresh heartbeats), a rescue branch that warned alive workers, and a separate
  `long_running_executions` warning loop. `reconcile_stuck_executions` failed only
  genuinely-dead workers and warned the rest.
- `processing/infrastructure/repositories/sa_processing_execution_repository.py` had
  `long_running_executions` + a `stale_running_executions` using a Text-column
  heartbeat comparison (`HEARTBEAT_RECENT_WINDOW_SECONDS * 2` = 180s cutoff).
- `processing/domain/repositories/processing_execution_repository.py` declared
  `long_running_executions` on the interface.
- `shared/infrastructure/events/processing_events.py` declared `EXECUTION_WARNING`.
- Frontend: `entities/processing/types.ts` (`warning` on `WorkflowProgress` +
  `'execution.warning'`), `shared/api/processingEvents.ts`, `ProcessingDrawer.tsx`
  (amber banner + stalled retry prompt + `now`/`dismissed` state), and its tests.

## Changes
- `tasks.py`: delete `HEARTBEAT_RECENT_WINDOW_SECONDS`, `_is_heartbeat_recent`,
  `_build_timeout_message`; add `_timeout_message(elapsed)` →
  `"Execution timed out after {elapsed}s. Check status or retry."`. `reconcile_stuck_executions`
  now calls `stale_running_executions(WORKER_JOB_TIMEOUT)` and fails each with the
  plain message + `EXECUTION_FAILED`. Update `process_execution_task` docstring.
- `sa_processing_execution_repository.py`: delete `long_running_executions`; simplify
  `stale_running_executions` to select RUNNING where `started_at` is not null and
  `started_at < now − older_than_seconds`.
- `processing_execution_repository.py`: remove `long_running_executions` from the interface.
- `processing_events.py`: remove `EXECUTION_WARNING`.
- `entities/processing/types.ts`: remove `warning?` from `WorkflowProgress` and
  `'execution.warning'` from `SSEEventType`.
- `shared/api/processingEvents.ts`: remove `'execution.warning'`.
- `ProcessingDrawer.tsx`: drop `now`/`dismissed` state + the 15s interval `useEffect`,
  remove `execution.warning` from the event handler, and simplify `WorkflowPanel`
  (remove `now`/`dismissed`/`onStallRetry`/`onStallDismiss`, the amber warning block,
  and the stalled retry prompt). Keep `WorkflowPanel` export + Failed-section error display.
- Docs: remove `## ProcessingExecutionWarning` from `docs/domain/processing/events.md`,
  update `EXECUTION_FAILED` to describe the reconcile timeout; delete
  `docs/ux/features/processing/long-running-warning.md`; update `docs/ux/DESIGN.md`
  wireframe, `docs/ux/README.md` index, and `docs/ux/features/jobs/page.md`.

## Testing Requirements
- `test_reconcile_long_running.py`: rewrite — RUNNING >600s → FAILED w/ timeout msg +
  `EXECUTION_FAILED`; RUNNING <600s → untouched.
- `test_tasks_timeout_message.py`: update to `_timeout_message(elapsed)` signature.
- `test_sa_processing_execution_repository.py`: replace `TestLongRunningExecutions`
  with `TestStaleRunningExecutions` (started_at-based).
- `ProcessingDrawer.test.tsx`: remove amber/stalled tests; keep WorkflowPanel render tests.
- Commands: `uv run pytest apps/backend/tests/shared/infrastructure/taskiq/ -v` and
  `uv run pytest apps/backend/tests/processing/infrastructure/repositories/ -v`;
  `cd apps/frontend && npx vitest run && npm run lint && npm run typecheck`.

## Constraints
Respect AGENTS.md: no raw SQL (SQLAlchemy only), no cross-context FKs, frontend TS only,
docs kept in sync. No DB migration needed (warning lived in existing `workflow_progress` JSONB).
