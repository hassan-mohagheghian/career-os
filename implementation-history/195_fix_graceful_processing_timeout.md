# Prompt 195 - Fix: graceful processing-timeout error UX in Job Detail drawer

## Objective

When a background processing execution fails after the `WORKER_JOB_TIMEOUT`
(600s) — marked failed by `reconcile_stuck_executions` — the Job Detail drawer
shows a bare red error line (`JobDetailDrawer.tsx:457`) only inside the
collapsed "Processing" section, appearing abruptly. Make the failure
state-managed and graceful: a prominent fade-in error banner with **Retry** and
**Check status** actions, plus a more precise backend timeout message.

## Current State

- `apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.tsx`:
  `ProcessingSection` renders `exec.error.message` with
  `text-2xs text-red-500 pt-1` (line ~457). It lives inside a `Collapsible`
  that is collapsed by default, so failures are easy to miss and "pop" in.
  The drawer header already has a `Reprocess` button (when `onReprocess` is
  supplied) but there is no in-context Retry/Check-status near the error.
- `apps/backend/shared/infrastructure/taskiq/tasks.py`:
  `reconcile_stuck_executions` (scheduled every 30s) fails RUNNING executions
  stale beyond `WORKER_JOB_TIMEOUT` (env-configurable, default 600) using a
  single generic message
  `f"Execution timed out after {WORKER_JOB_TIMEOUT}s (worker crash suspected)"`
  (line ~115). It already emits `EXECUTION_FAILED` over SSE with the message.
- Heartbeats already exist (`execution_runner._start_heartbeat`,
  `HEARTBEAT_INTERVAL_SECONDS = 30`; `stale_running_executions` uses
  `heartbeat_at`). SSE push (`/events/processing`) is the async channel, so a
  `202 + polling` rewrite is unnecessary — the architecture already satisfies
  the "communication" goal of the resolution strategy.
- Animation utility `tailwindcss-animate` is active (components use
  `animate-in` / `fade-in-0` / `zoom-in-95`), so a fade-in requires no new CSS.

## Changes

### Frontend (`JobDetailDrawer.tsx`)
1. Thread `onReprocess?: (id: string) => void` from `JobDetailDrawer` →
   `JobDetailContent` (currently only the header button uses it).
2. Add a `ProcessingErrorBanner` rendered at the top of `JobDetailContent` when
   `detail.latest_processing_execution?.status === 'failed'` and an error
   message exists. Markup: destructive-tinted card with `XCircle` icon, the
   error message (`break-words`), and two actions:
   - **Retry** → `onReprocess?.(detail.id)` (hidden when no `onReprocess`).
   - **Check status** → `queryClient.invalidateQueries({ queryKey: ['job-detail', detail.id] })`
     (refetches the detail).
3. Apply `animate-in fade-in-0 duration-300` to the banner and to the existing
   in-section error line so neither "pops" in.
4. Import `ArrowsClockwise` from `@phosphor-icons/react` (XCircle, Repeat already
   imported).

### Backend (`tasks.py`)
5. Add a module-level pure helper
   `_build_timeout_message(heartbeat_at, timeout) -> str` that returns a precise
   message: if `heartbeat_at` is recent (< ~3 heartbeats) the worker is still
   reporting progress (slow/stuck); otherwise it stopped responding (crash/OOM).
   Handle `heartbeat_at` being `datetime` or ISO string.
6. Use it in `reconcile_stuck_executions` instead of the hard-coded f-string.
   Keep the SSE `EXECUTION_FAILED` emit and structured logging.

### Tests
7. Frontend `JobDetailDrawer.test.tsx`: render a detail with a failed execution
   + error; assert the banner shows the message and an `animate-in` class;
   clicking **Retry** calls `onReprocess('job-1')`; clicking **Check status**
   triggers a second `jobApi.getDetail` call.
8. Backend: new `test_tasks_timeout_message.py` unit-testing `_build_timeout_message`
   for both the stale (crash) and recent-heartbeat (slow/stuck) branches — no DB.

### Docs
9. `docs/ux/features/jobs/page.md`: add `## Processing Failure Banner` with an
   ASCII wireframe; note the error fade-in and Retry/Check-status actions.

## Testing Requirements

- `cd apps/frontend && npx vitest run src/features/jobs-v2/components/JobDetailDrawer.test.tsx` pass; `npm run lint` + `npm run typecheck` clean for touched files.
- `uv run pytest apps/backend/tests/shared/infrastructure/taskiq/test_tasks_timeout_message.py -v` pass.
- Manual: open a job whose latest execution failed → banner fades in with the
  precise message; Retry reprocesses; Check status refetches.

## Constraints

- Respect AGENTS.md rule 13 (UX docs + wireframe).
- No new CSS framework deps; reuse `tailwindcss-animate` utilities.
- Do not rewrite the SSE/worker architecture (already correct); only refine the
  message + UI. Keep `WORKER_JOB_TIMEOUT` env-configurable.
- Cross-context rule unchanged: backend timeout logic stays in `shared` taskiq
  layer; frontend reads execution state from the jobs detail API.
