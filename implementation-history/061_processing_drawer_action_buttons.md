# Prompt 061 - Action Buttons For Each Job Type In The Processing Drawer

## Objective

Add per-entry action buttons to the Processing Queue Drawer so users can act on
executions directly from the queue.

The drawer currently shows three queue sections — Running, Waiting, Failed —
each with a job title, current step/status, links and the workflow panel, but
no way to act on an entry.

Add a small action row per entry with the buttons that make sense for that
entry's status, using the existing Processing API. All cards must have a delete
(remove) button (AGENTS.md rule 9).

---

# Read Documentation First

Before making changes read:

- docs/api/processing/get-processing-queue.md
- docs/api/processing/cancel-processing.md
- docs/api/processing/retry-processing.md
- docs/api/processing/remove-processing-queue-entry.md
- docs/api/sse/processing-events.md
- docs/ux/features/jobs/processing-queue.md
- apps/frontend/src/features/jobs-v2/components/ProcessingDrawer.tsx
- apps/frontend/src/entities/processing/api.ts
- apps/frontend/src/entities/processing/types.ts

---

# Current State

`ProcessingDrawer.tsx` loads a `QueueSnapshot` (`processing` / `queued` /
`failed`) and renders each entry through `QueueSection`. No action buttons.

The API client already exposes every needed operation:

- `processingApi.cancel(id)`  → `POST /api/processing/executions/{id}/cancel`
- `processingApi.retry(id)`   → `POST /api/processing/executions/{id}/retry`
- `processingApi.removeQueueEntry(id)` → `DELETE /api/processing/queue/{id}`

Queue entries expose `execution_id`, `status`, `error`, `current_step`.

---

# Implementation Steps

## 1. Per-Status Action Buttons

Add a compact action row to each queue entry card. Mapping:

| Section   | Entry status            | Buttons                                     |
| --------- | ----------------------- | ------------------------------------------- |
| Running   | running                 | Cancel, Remove (stop event propagation)     |
| Waiting   | queued / starting       | Cancel, Remove                              |
| Failed    | failed                  | Retry, Remove                               |

Rules:

- `Remove` is available for every entry (AGENTS.md: all cards need a delete
  button). For running entries it stops propagation so the running worker is
  first cancelled via `cancel`; the Remove endpoint itself refuses running
  executions.
- `Retry` only for `failed`.
- `Cancel` only for `running` / `queued` / `starting`.
- Disable buttons while the request is in flight for that entry.
- Reuse the existing Phosphor icons (`Square`, `ArrowsClockwise`, `X`) and the
  `Button` / `Tooltip` UI kit, matching the compact icon style used in
  `JobActions.tsx`.

## 2. State Refresh After An Action

After a successful action:

- `cancel` / `retry` / `remove` → reload the queue snapshot (`processingApi.queue`)
  so the section counts and list stay correct.
- Keep SSE subscriptions wired; avoid duplicate refreshes if the SSE handler
  already reloads after `queue.entry.removed`.

## 3. Error Handling

Show a transient error if an action fails (e.g. `remove` on a running entry
returns 409). Do not crash the drawer.

---

# Testing Requirements

Frontend:

- Tests for `ProcessingDrawer`:
  - Running entry renders Cancel and Remove.
  - Queued entry renders Cancel and Remove.
  - Failed entry renders Retry and Remove.
  - Buttons call the matching `processingApi` method and reload the snapshot.
- Run `npx vitest run` in `apps/frontend`.

---

# Important Constraints

- Do not add new backend endpoints; reuse `cancel` / `retry` / `removeQueueEntry`.
- Do not change the queue API contract.
- Do not render raw node/worker names.
- Follow accessibility basics: icon buttons carry `aria-label` + `Tooltip`.
