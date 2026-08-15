# Prompt 162 - Job Tracking Status

## Objective

Surface the application-funnel lifecycle (not applied → applied → interview → offer → accepted / rejected / withdrawn) as a tracking status on the jobs list (new column + filter) and in the job drawers, so the user can see at a glance where each job stands without opening the application workspace.

## Current State

- Applications carry the funnel status enum `recommended / preparing / ready_to_apply / applied / rejected / withdrawn` in `apps/backend/applications/domain/entities/application.py:27` (`ApplicationStatus`). It lacks `interview`, `offer`, `accepted`.
- The jobs list response (`apps/backend/jobs/presentation/api/jobs_v2_router.py:204` `list_jobs_v2` → `JobListItemSchema`) has no tracking field and no cross-reference to application state.
- The job list only reflects `processing_executions.status` (the existing "Status" column).
- Frontend application status rendering lives in `apps/frontend/src/entities/application/types.ts` (values) and `apps/frontend/src/features/job-application/components/ApplicationStatusBadge.tsx` / `ApplicationTracker.tsx`.
- The jobs router already depends on `get_application_repo` (line 46-53), so aggregating application status per job is bounded-context-safe (logical `job_id` ref only, AGENTS.md rule 15).

## Changes

- `apps/backend/applications/domain/entities/application.py`: add `INTERVIEW`, `OFFER`, `ACCEPTED` to `ApplicationStatus` + `ALL`.
- `apps/backend/applications/domain/repositories/application_repository.py` + `apps/backend/applications/infrastructure/repositories/sa_application_repository.py`: add `statuses_by_job_ids(job_ids) -> dict[str, str]` and `job_ids_with_application() -> list[str]`.
- `apps/backend/jobs/presentation/api/schemas/jobs_v2.py`: add `tracking_status: str | None` to `JobListItemSchema`.
- `apps/backend/jobs/presentation/api/jobs_v2_router.py`:
  - `_v2_job_to_schema`: accept `tracking_status` and set it on the schema.
  - `list_jobs_v2`: add `tracking_status: str | None` query param; resolve to `job_ids` (specific status) or `exclude_job_ids` (`not_applied`) via the application repo; attach `tracking_status` to each item via `statuses_by_job_ids`.
- Frontend:
  - `apps/frontend/src/entities/job/types.ts`: add `tracking_status` to the job list item type + tracking status value set.
  - `apps/frontend/src/features/jobs-v2/components/JobsTable.tsx`: add a **Tracking** badge column.
  - `apps/frontend/src/features/jobs-v2/components/JobsToolbar.tsx` + `apps/frontend/src/entities/job/api.ts` (or the infinite-query hook): add a **Tracking** filter mapped to the `tracking_status` query param.
  - `apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.tsx` / `JobEditDrawer.tsx`: display the tracking badge (read-only).
  - `apps/frontend/src/entities/application/types.ts` + `ApplicationStatusBadge.tsx` + `ApplicationTracker.tsx`: add `interview`, `offer`, `accepted` values/labels/colors.

## Testing Requirements

- Backend: unit tests for the app repo `statuses_by_job_ids` / `job_ids_with_application`; router test asserting the `tracking_status` filter and per-item `tracking_status` in the list response. Run `uv run pytest apps/backend/tests/ -v`.
- Frontend: vitest tests for the Tracking column + filter (JobsPage.test) and the new badge values. Run `cd apps/frontend && npx vitest run`.
- Docs: update `docs/ux/features/applications/workspace.md`, add a tracking section/wireframe, `docs/ux/DESIGN.md`, and the API list docs.

## Constraints

- Respect AGENTS.md rules 7 (newest first), 15 (logical ref, no cross-context FK — application status read via repo, not a join), 13 (wireframe docs for the UI change), 14 (only migrate if a DB column changes — none here, status is free string).
- No new field on the job; application status is the source of truth.
