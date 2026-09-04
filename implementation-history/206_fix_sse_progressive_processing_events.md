# Prompt 206 - Fix SSE Progressive Processing Events in Docker/Terraform

## Objective
Job/company processing in the terraform-docker deployment shows no live progress:
no `execution.started` / `workflow.step.*` updates during the run; only the
completed state appears after a manual page refresh. Make processing events
stream progressively end-to-end (worker → Redis → backend SSE → frontend).

## Current State
- Worker publishes lifecycle + per-step events to Redis pub/sub
  (`apps/backend/shared/infrastructure/events/processing_events.py`,
  `processing/application/workflows/progress_ops.py`).
- Backend streams them at `GET /events/processing?token=...`
  (`apps/backend/shared/presentation/api/processing_events_router.py`).
- Frontend subscribes via `EventSource` in
  `apps/frontend/src/shared/api/processingEvents.ts` using
  `SSE_BASE = ${NEXT_PUBLIC_API_URL}/events/processing`.
- Problems:
  1. `NEXT_PUBLIC_*` is baked at frontend **build** time. The terraform
     `frontend` image is prebuilt, so a stale/empty value points EventSource
     at the wrong origin (frontend origin → 404, or cross-origin stream
     killed by proxies) → no live events, refresh shows final DB state.
  2. `next.config.ts` has no `rewrites()` for `/api/*` or `/events/*`, so a
     same-origin relative URL has nowhere to go.
  3. SSE handler never yields keepalive bytes; idle streams through docker
     networking/proxies can stall without triggering EventSource reconnect.

## Implementation Steps
1. `apps/frontend/src/shared/api/processingEvents.ts`: connect directly to
   `${NEXT_PUBLIC_API_URL}/events/processing` when baked in (local dev —
   avoids the Next dev-proxy gzip buffering); fall back to same-origin
   relative `/events/processing` when the env is empty (prebuilt
   terraform-docker image, where `NEXT_PUBLIC_*` cannot be injected at
   container runtime).
2. `apps/frontend/next.config.ts`: add `rewrites()` proxying `/api/:path*`
   and `/events/:path*` to `${BACKEND_URL:-http://localhost:5000}` so the
   same-origin fallback works in the standalone docker frontend (production
   proxy streams without compression; dev keeps the direct connection).
3. `apps/backend/shared/presentation/api/processing_events_router.py`: emit
   an initial `: connected` SSE comment and periodic `: ping` keepalive
   comments so intermediaries don't buffer/close the idle stream.
4. Docs: updated `docs/api/sse/processing-events.md` subscription section
   (direct-vs-rewrite rule + keepalive). No layout change → no wireframe.

## Testing Requirements
- `cd apps/frontend && npx vitest run` (SSE subscription tests).
- `uv run pytest apps/backend/tests/ -v -k "processing or sse or events"`.
- Manual e2e (needs user go-ahead to start servers): terraform docker stack
  up, open frontend, process the jobinja JD URL, observe `running` badge +
  step progress live without refresh.

## Constraints
- Do not change the SSE wire contract (`event:` names, `data` envelope).
- Do not add cross-context FKs; no model changes.
- Keep `NEXT_PUBLIC_API_URL` support for REST (`http-client.ts` already
  falls back to relative `/api`).

## E2E Result (terraform-docker, 2026-09-04, jobinja Node.js JD)
- Job `01a06b3c…` (execution `fe68905f…`): `execution.created → started →
  ~20× workflow.step.started/progress/completed → execution.completed`,
  every event timestamped the same second it was emitted — fully live, no
  refresh. Persisted: title/role/location/work-types, company link
  (Nik Modern), scores fit 38 / success 85 / overall 57.
- Company `01a06b41…` reprocess (`a8db5dcd…`): live steps then
  `execution.failed` in 3 s — correct business failure (`validate_context`:
  company has no fetchable sources/links), and the failure itself streamed
  instantly.
- Infra note (not fixed here): one TaskIQ worker died once on
  `redis TimeoutError reading` in the broker listen loop, losing the
  in-flight task (execution stuck RUNNING until cancelled; reconcile only
  fails RUNNING after `WORKER_JOB_TIMEOUT=600s` and TaskIQ does not
  autoclaim pending stream messages). If it recurs, look at
  `RedisStreamBroker` socket options / autoclaim in
  `shared/infrastructure/taskiq/config.py` + `client.py`.
