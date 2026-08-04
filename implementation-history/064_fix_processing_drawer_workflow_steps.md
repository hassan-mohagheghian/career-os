# Prompt 064 - Fix Empty Workflow Steps in the Processing Drawer

## Objective

Fix the Processing Drawer showing "No steps recorded yet." and an empty
progress bar for a job that is actively running.

Root cause is a frontend state race in `ProcessingDrawer.tsx`: the drawer is
opened before the execution starts, so its `GET /processing/executions/{id}`
returns `workflow: null` (the backend only persists `workflow_progress` once the
runner begins). That null is cached and the SSE merge handler drops every
`workflow.step.*` event (`if (!existing) return prev`), so the workflow stays
null for the entire run.

Scope: frontend only. The backend is the source of truth and already emits all
step events; the drawer just needs to bootstrap its workflow state once the
execution begins.

---

## Current State

- `ProcessingDrawer.tsx` fetches each execution's workflow once when the drawer
  opens and caches the result in `loadedRef`; a null result is never retried.
- The SSE handler only merges step events into an already-loaded (non-null)
  workflow; events arriving with a null cached workflow are silently dropped.
- `workflow.step.*` events carry only the per-step data — the overall
  `workflow.progress` is not included, so the top progress bar does not advance
  during a run (REST progress is only persisted at start/completion).
- Backend persists the initial 13-step tree at `execution.started` and the final
  tree at `execution.completed`/`execution.failed`, then emits lifecycle events —
  so a refetch triggered by those events always returns a real workflow.

---

# Implementation Steps

## Frontend — ProcessingDrawer.tsx

1. Add `workflowsRef` (a ref mirror of the `workflows` state) and a
   `setWorkflow(id, wf)` helper so the SSE callback can read the current
   workflow synchronously.
2. Add `inFlightRef` to dedupe concurrent `loadWorkflow` fetches.
3. `loadWorkflow`: skip when a workflow already exists for the id, a fetch is in
   flight, or the id is cached in `loadedRef`; on success cache the result in
   `loadedRef` and only store non-null workflows.
4. Add `ensureWorkflow(id)` = clear the id from `loadedRef` + `loadWorkflow(id)`.
5. SSE handler changes:
   - Step events (`workflow.step.started|progress|completed|failed`): if no
     workflow is cached for the execution, call `ensureWorkflow` (bootstrap);
     otherwise merge via `mergeWorkflowStep`.
   - Lifecycle events (`execution.started|completed|failed|cancelled`): call
     `ensureWorkflow` only when no workflow is cached yet (never refetch when
     one exists — avoids clobbering live SSE-merged progress with the stale
     initial REST tree), then `loadSnapshot()`.
   - `queue.entry.removed`: clear the cached workflow + `loadSnapshot()`.

## Frontend — workflowMerge.ts

After merging a step, recompute the overall `workflow.progress` from the
displayable steps, mirroring the backend `_recompute` (average of displayable
steps; `completed`/`failed`/`skipped` count as 100, otherwise `step.progress ?? 0`,
rounded to one decimal). Keeps the top progress bar live during a run.

## Tests

- `ProcessingDrawer.test.tsx`: capture the SSE listener in the mock; add a
  regression test where `processingApi.get` returns `{ workflow: null }` first,
  then a real workflow after `execution.started`, and assert the step titles
  render (no "No steps recorded yet."). Add a self-heal test: a step event with
  no cached workflow triggers a second `get` call.
- `workflowMerge.test.ts`: assert `progress` is recomputed after a merge.

## Docs

- `docs/ux/features/jobs/processing-queue.md` — note that the drawer bootstraps
  workflow state from the first `execution.started` / step event when opened
  before processing starts.
- `docs/architecture/frontend-sync.md` — note the one-shot workflow refetch on
  lifecycle/step bootstrap in the event recovery section.

---

# Testing Requirements

- `cd apps/frontend && npx vitest run` passes.
- `cd apps/frontend && npm run lint` passes.
- `cd apps/frontend && npm run typecheck` passes.

---

# Important Constraints

- Frontend-only change; no backend edits, no API contract changes.
- The drawer must never clobber live SSE-merged progress with a stale REST
  snapshot — only bootstrap when no workflow data exists yet.
- No new runtime dependencies; keep the change to the two frontend modules plus
  tests and docs.
