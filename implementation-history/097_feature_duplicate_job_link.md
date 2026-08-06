# Prompt 097 - Link to Existing Job on Duplicate URL

## Objective

When importing a job whose primary URL already exists, the Add Job drawer
currently shows a plain error ("A Job with the same primary URL already
exists."). Make the error actionable: the backend returns the existing job's id
in the 409 error details, and the drawer renders a link ("Open existing job")
that navigates to `/jobs?job=<id>`, opening the existing job's detail drawer.

## Current State

- `POST /api/jobs` raises `JobAlreadyExistsError` (409, code
  `JOB_ALREADY_EXISTS`) with no job reference when `get_by_url` finds a
  non-deleted job (jobs_router.py:66-68).
- The shared error handler serializes `exc.details` (error_handler.py), so a
  `job_id` in `details` reaches the frontend for free.
- `useCreateJob` only extracts `error.message` as a string; `CreateEntityDrawer`
  renders `error` as plain text.
- The Jobs page opens a job drawer from a URL via `/jobs?job=<id>`
  (jobs-page-v2/index.tsx:115-118), and `onOpenJob` uses the same href
  (companies-page adapter).

## Design Decision

Return `details: { job_id }` from the 409 and render a link in the drawer error
box. The link is a normal anchor to `/jobs?job=<id>` so navigating (or opening
in a new tab) opens the existing job's detail drawer.

## Implementation Steps

1. **Backend**:
   - `JobAlreadyExistsError` accepts an optional `job_id` and sets
     `details={"job_id": ...}`.
   - `create_job` raises `JobAlreadyExistsError(job_id=existing["id"])`.
2. **Frontend**:
   - `useCreateJob`: parse `body.error.details.job_id` into `existingJobId`
     state; expose it from the hook.
   - `CreateEntityDrawer`: add optional `errorLink?: { label, href } | null`
     prop rendered as a link inside the error box.
   - `JobsPage`: pass `errorLink` pointing to `/jobs?job=<id>` when
     `existingJobId` is set.
3. **Tests**:
   - Backend: `test_create_duplicate_url_returns_409` asserts
     `error.details.job_id` equals the first job's id.
   - Frontend: `useCreateJob` test parsing `existingJobId`; drawer test that
     the error link renders when `errorLink` is provided.
4. **Docs**: `docs/api/jobs/` duplicate-URL response example, `DESIGN.md`/
   `docs/ux/features/jobs/page.md` Add Job error state.

## Testing Requirements

- `uv run pytest apps/backend/tests/ -q` green.
- `cd apps/frontend && npx vitest run` green (typecheck/lint pre-existing
  failures untouched).

## Constraints

- Keep the error message text unchanged (tests rely on it).
- Do not add API routes to `entrypoints/api.py`.
- AGENTS.md rule 13: UX wireframes must be updated.
