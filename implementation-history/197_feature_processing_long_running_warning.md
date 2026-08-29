# Prompt 197 - Long-running worker warning + client-side stalled retry

## Objective

Alive-but-slow background processing executions are currently invisible past the
600s soft budget: `reconcile_stuck_executions` only *fails* RUNNING executions
whose heartbeat is stale (see #188/#195), so a worker that keeps heartbeating
but is genuinely stuck/slow at 0% progress runs forever with no UI signal. If the
heartbeat thread ever stalls, the failure message is misleading. Fix: surface a
**non-terminal** warning for RUNNING executions that exceed `WORKER_JOB_TIMEOUT`
while still heartbeating, and let the frontend offer a manual **Retry** when
progress is stuck at 0%.

## Current State

- `apps/backend/shared/infrastructure/taskiq/tasks.py:38` — `HEARTBEAT_RECENT_WINDOW_SECONDS = 90`.
- `apps/backend/shared/infrastructure/taskiq/tasks.py:41` — `_build_timeout_message(heartbeat_at, timeout)` returns the precise "exceeded 600s but the worker is still reporting progress" text for a *recent* heartbeat.
- `apps/backend/shared/infrastructure/taskiq/tasks.py:139` — `reconcile_stuck_executions` calls `stale_running_executions(WORKER_JOB_TIMEOUT)` and *fails* the result. `stale_running_executions` is heartbeat-based, so fresh-heartbeat workers are not returned and are therefore never warned either.
- `apps/backend/processing/domain/repositories/processing_execution_repository.py:77` — interface has `stale_running_executions` only.
- `apps/backend/processing/infrastructure/repositories/sa_processing_execution_repository.py:277` — `stale_running_executions` implementation (heartbeat-based).
- `apps/backend/shared/infrastructure/events/processing_events.py:46` — execution lifecycle events; no warning event.
- `apps/backend/processing/application/services/processing_queue_service.py:47` — `workflow_progress` (a JSONB dict) is already returned to the frontend, so a `warning` key survives snapshot re-fetches without a migration.
- `apps/frontend/src/shared/components/ProcessingDrawer.tsx:139` — `WorkflowPanel` renders `entry.error` (red) only.
- `apps/frontend/src/entities/processing/types.ts:24` — `WorkflowProgress` has no `warning`; `SSEEventType` has no `execution.warning`.
- `apps/frontend/src/shared/api/processingEvents.ts:5` — `EVENT_TYPES` list (no warning).

## Changes

### Backend

1. **`processing_events.py`** — add `EXECUTION_WARNING = "execution.warning"` next to `EXECUTION_FAILED`.

2. **`processing_execution_repository.py`** (interface) — add abstract
   `long_running_executions(older_than_seconds: int = 600, fresh_heartbeat_seconds: int = 90) -> list[ProcessingExecution]`.

3. **`sa_processing_execution_repository.py`** — implement `long_running_executions`:
   return RUNNING rows where `started_at < now - older_than_seconds` AND
   `heartbeat_at` is not null AND `heartbeat_at >= now - fresh_heartbeat_seconds`.
   (Uses `inspect`/plain query; no raw SQL per AGENTS.md rule 2.)

4. **`tasks.py`** — in `reconcile_stuck_executions`:
   - Detect *dead* workers with `stale_running_executions(HEARTBEAT_RECENT_WINDOW_SECONDS * 2)` (≈180s) → fail as today (keeps "worker stopped responding" branch).
   - NEW: `long_running = repo.long_running_executions(WORKER_JOB_TIMEOUT, HEARTBEAT_RECENT_WINDOW_SECONDS)`. For each, do **not** fail. Set `execution.workflow_progress["warning"] = _build_timeout_message(execution.heartbeat_at, WORKER_JOB_TIMEOUT)` (the "still reporting progress" text, now used as a warning), `repo.save`, and `await processing_events.publish(EXECUTION_WARNING, ...)` with `message=...`. Log at info level.

### Frontend

5. **`types.ts`** — add `warning?: string | null` to `WorkflowProgress`; add `'execution.warning'` to `SSEEventType`.

6. **`processingEvents.ts`** — add `'execution.warning'` to `EVENT_TYPES`.

7. **`ProcessingDrawer.tsx`**:
   - `WorkflowPanel`: render an amber banner (`text-amber-500`) when `workflow?.warning` is present (above the existing red `entry.error`).
   - Subscribe handler: on `execution.warning`, set `workflowsRef.current[id].warning` and update state (via `setWorkflow` with the existing workflow or a bootstrapped one).
   - Stalled retry: keep a `dismissedRef = useRef<Set<string>>(new Set())` and a `now` state ticking every 15s while open. For each RUNNING `entry`, if `now - started_at > WORKER_JOB_TIMEOUT (600s)` and `Number(entry.progress) === 0` and not dismissed → render a non-destructive "Job appears stalled — Retry?" prompt with a **Retry** button (reuse `handleRetry`) and **Dismiss** (adds id to `dismissedRef`).

## Testing Requirements

- Backend:
  - `apps/backend/tests/processing/infrastructure/repositories/test_sa_processing_execution_repository.py` — add `long_running_executions` cases: fresh-heartbeat + started>600s → returned; stale heartbeat → not; not-running → not; recent start → not.
  - `apps/backend/tests/shared/infrastructure/taskiq/test_tasks_timeout_message.py` — keep. Add `test_reconcile_warns_long_running_not_fails` (unit, monkeypatch repo) asserting a heartbeating >600s execution is NOT failed and warning is set + `EXECUTION_WARNING` published.
- Frontend:
  - `apps/frontend/src/shared/components/ProcessingDrawer.test.tsx` (new) — assert amber warning banner renders for a workflow with `warning`, and that a RUNNING entry stuck >600s at 0% shows the retry prompt and Dismiss suppresses it.
- Commands: `uv run pytest apps/backend/tests/processing/infrastructure/repositories/test_sa_processing_execution_repository.py apps/backend/tests/shared/infrastructure/taskiq/ -v` and `cd apps/frontend && npx vitest run src/shared/components/ProcessingDrawer.test.tsx`. Also `npm run lint` + `npm run typecheck`.

## Constraints

- No cross-context FK changes; no new DB migration (warning lives in existing `workflow_progress` JSONB).
- No raw SQL (AGENTS.md rule 2); use SQLAlchemy ORM.
- Best-effort event publishing; warning must never change business behavior (runner still completes/fails on its own).
- AGENTS.md rule 13: add `docs/ux/features/processing/long-running-warning.md` wireframe (warning vs error + stalled prompt) and update `docs/ux/README.md` + `docs/ux/DESIGN.md`; add `execution.warning` to `docs/domain/processing/events.md`.
- Keep `WORKER_JOB_TIMEOUT` env-configurable.
