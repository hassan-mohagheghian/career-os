# Prompt 174 - Application Status Timeline

## Objective

Give every application a per-state date so the user can trace the timeline of
status transitions. Today the tracker only has a single `applied_at` date; add a
`status_timeline` (one entry per status, each with a `changed_at`). When a new
status is selected the change time defaults to **now** (set by the backend), and
the user can adjust each entry's time afterwards. The timeline renders as a
dedicated box inside the Application Tracker, where each node's time can be
edited and a node can be **deleted**. The separate "Applied at" field is removed
(the `applied` status time lives in the timeline).

## Current State

- `Application` entity (`apps/backend/applications/domain/entities/application.py:68`)
  has only `status` + `applied_at`. `ApplicationService.update`
  (`application_service.py:59`) updates `status`/`applied_at`; `_UPDATABLE`
  only checks those two keys.
- Schema: `application.applications`, children `application_follow_ups`,
  `application_documents` (`application_model.py:29`). Application delete
  cascade lists only follow-ups + documents (`sa_application_repository.py:90`).
- API `PATCH /api/applications/{id}` body `{status?, applied_at?}`
  (`UpdateApplicationRequest`, `schemas/applications.py:23`); detail response
  has no timeline. Tracker (`ApplicationTracker.tsx`) has Status select + Applied
  at + follow-ups; no timeline box.

## Changes

### Backend

- `domain/entities/application.py` — add `ApplicationStatusEvent` dataclass
  (`id`, `application_id`, `status`, `changed_at`, `created_at`, `updated_at`,
  `to_dict()`); export it.
- `domain/events.py` — add `ApplicationStatusChanged` event
  (`application_id`, `status`, `changed_at`) and `ApplicationStatusRemoved`
  (`application_id`, `status`).
- `infrastructure/models/application_model.py` — add
  `ApplicationStatusEventModel` (`application.application_status_timeline`,
  FK to `application.applications.id`).
- `infrastructure/mappers.py` — add `status_event_model_to_dict` /
  `dict_to_status_event_model`.
- `domain/repositories/status_event_repository.py` — new `IStatusEventRepository`
  (`create`, `list_for_application` ordered by `changed_at`, `get_by_id`,
  `update` for `changed_at`, `delete`).
- `infrastructure/repositories/sa_status_event_repository.py` — SA impl.
- `infrastructure/__init__.py` — export model + repo.
- `application/services/application_service.py` — constructor gains optional
  `timeline_repo=None` (after `event_publisher`). On `create`, write an initial
  `recommended` status event with `changed_at=now`. On `update`, when `status`
  changes from current, write a status event with
  `changed_at = data.get("timeline_at") or now` and emit `ApplicationStatusChanged`.
  Add `timeline_at` to `_UPDATABLE`-relevant handling.
- `application/services/status_event_service.py` — new `StatusEventService`
  (`update_changed_at`, `delete`, both emit the relevant event), mirroring
  `FollowUpService`.
- `presentation/api/schemas/applications.py` — add `timeline_at` to
  `UpdateApplicationRequest`; add `ApplicationStatusEventSchema` +
  `status_timeline` to `ApplicationDetailResponse`; extend
  `build_detail_response` to accept the timeline list.
- `presentation/api/applications_router.py` — thread `status_event_repo` into
  detail builders; add `PATCH /api/applications/timeline/{timeline_id}`
  (`{changed_at}`) and `DELETE /api/applications/timeline/{timeline_id}` (204).
  Wire delete cascade for the new model.
- `dependencies.py` — add `get_status_event_repo` + `get_status_event_service`.
- Alembic autogenerate `application_004_add_status_timeline` (new table).

### Frontend

- `entities/application/types.ts` — add `ApplicationStatusEvent` +
  `status_timeline` on `ApplicationDetail`; `timeline_at?` on
  `UpdateApplicationInput`; `UpdateTimelineInput { changed_at }`.
- `entities/application/api.ts` — `updateTimeline(timelineId, changedAt)` and
  `deleteTimeline(timelineId)`.
- `entities/application/hooks.ts` — `useUpdateTimelineMutation`,
  `useDeleteTimelineMutation`.
- `features/job-application/components/ApplicationTracker.tsx` — Status select
  sends `{status}` (backend stamps `changed_at=now`); remove the separate
  "Applied at" field; add an **Application Timeline** box listing each status
  event (badge + `changed_at` as an editable `datetime-local` input committing
  via `updateTimeline` + a trash delete button via `deleteTimeline`).

## Testing Requirements

- Backend `tests/applications/domain/test_application_services.py` — fake
  timeline repo; assert create writes a `recommended` event and status change
  writes an event with default-now + `timeline_at` override + emits
  `ApplicationStatusChanged`; `StatusEventService.delete` removes the row and
  emits `ApplicationStatusRemoved`.
- Backend `tests/applications/presentation/api/test_applications_router.py` —
  create/patch returns `status_timeline`; patch with `timeline_at` sets
  `changed_at`; `PATCH /timeline/{id}` updates `changed_at`; `DELETE
  /timeline/{id}` removes the row (204).
- Frontend `ApplicationTracker.test.tsx` — renders timeline box (no "Applied at"
  field); status change calls `update` with `{status}`; editing a timeline
  `changed_at` calls `updateTimeline`; deleting a node calls `deleteTimeline`.
- Run: `uv run pytest apps/backend/tests/applications/ -v`,
  `cd apps/frontend && npx vitest run`, `npm run lint`, `npm run typecheck`.

## Constraints

- Timeline table lives in the `application` schema; FK only within context (rule 15).
- No raw SQL (rule 2); no new routes in `entrypoints/api.py` (rule 10).
- EDD rule 16: define + emit + document `ApplicationStatusChanged`.
- Rule 13: document the UI change with an ASCII wireframe + Mermaid diagram under
  `docs/ux/features/applications/application-tracker.md` and update the
  `docs/ux/README.md` index.
- Use Alembic autogenerate for the migration, then tune (rule 14).