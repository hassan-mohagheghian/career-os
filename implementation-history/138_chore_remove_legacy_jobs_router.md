# Prompt 138 - Remove legacy jobs router and list use case

## Objective

Remove the last legacy jobs module pieces so the app is fully on the V2 jobs
API:

- `apps/backend/jobs/application/use_cases/list_jobs.py` — dead code (the CLI
  `list` command calls `job_repo.list_jobs` directly; nothing imports
  `ListJobsUseCase`).
- `apps/backend/jobs/presentation/api/jobs_router.py` — its only endpoint is
  `POST /api/jobs` (Add Job Drawer create). The V2 router owns list/detail/
  update/delete, so the create endpoint moves there first, then the file is
  deleted.

## Current State

- `jobs_router.py` is included in `shared/presentation/api/root_router.py:45`
  with `prefix="/jobs"`, `tags=["jobs"]`, and registers `POST ""` →
  `create_job`.
- The frontend `useCreateJob` (`apps/frontend/src/features/jobs/hooks/
  useCreateJob.ts`) calls `POST /api/jobs` with the same body the V2 schemas
  describe (`job_post_url`, `job_title`, `links`, `notes`, `queue`).
- `jobs_v2_router.py` is registered **before** the legacy router
  (`root_router.py:38`), so moving the create route there keeps the exact same
  path `POST /api/jobs` with no frontend change.

## Changes

- Move `create_job` and its `_queue_job_for_processing` helper from
  `jobs_router.py` into `jobs_v2_router.py` (registered at `POST ""` under the
  `/jobs` prefix; same `201` behavior, same `JobAlreadyExistsError` dedup via
  `find_duplicate_job`).
- Delete `apps/backend/jobs/presentation/api/jobs_router.py`.
- Delete `apps/backend/jobs/application/use_cases/list_jobs.py`.
- Update `shared/presentation/api/root_router.py`: drop the
  `from jobs.presentation.api.jobs_router import router as jobs_router` import
  and the `include_router(jobs_router, ...)` line.
- Update docs that reference `jobs_router` / the legacy list use case
  (`docs/api/api-design.md`, `docs/architecture/backend-structure.md`,
  `docs/architecture/code-ownership-map.md`,
  `docs/architecture/folder-structure.md`, `docs/api/jobs/create-job.md`).

## Testing Requirements

- Existing `apps/backend/tests/jobs/presentation/api/test_create_job.py` hits
  `POST /api/jobs` and must keep passing unchanged (proves the route survived
  the move).
- Run `uv run pytest apps/backend/tests/jobs/ -v`.
- Grep to confirm no remaining references to `jobs_router` /
  `ListJobsUseCase` in `apps/backend/`.

## Constraints

- No schema change, no migration, no new domain events, no version bump.
- Do **not** touch the frontend — `POST /api/jobs` path and payload stay
  identical.
- Keep the create endpoint's `201` response shape (`CreateJobResponse`) and the
  `JobAlreadyExistsError` `details.job_id` payload unchanged.
