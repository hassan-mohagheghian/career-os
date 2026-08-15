# Prompt 160 - Job application page buttons + duplicate error links to application

## Objective

Two UX changes around jobs and the job application workspace:

1. When a job import hits an already-existing job, the error note shown to the
   user ("A Job with the same primary URL already exists.") must link to the
   existing job's **application** page. It must NOT save any new note to the
   job's notes.
2. Add **Job Detail** and **Job Edit** buttons to the job application workspace
   page (`/jobs/{job_id}/application`) so the user can view/edit the job
   without leaving the application page.

## Current state

- `POST /api/jobs` returns 409 `JOB_ALREADY_EXISTS` with `details.job_id` when
  a duplicate is detected; the provided notes are discarded (no note is saved).
- `apps/frontend/src/features/jobs-v2/components/JobsPage.tsx` maps that error
  to `errorLink={{ label: 'Open existing job', href: '/jobs?job={id}' }}`,
  which the `CreateEntityDrawer` renders as a link after the error text. That
  link goes to the Jobs page detail, not the application page.
- `apps/frontend/src/features/job-application/components/WorkspaceHeader.tsx`
  (the application page header) currently shows only a "Back to Job" link and
  an "Open job posting" link. There are no Job Detail / Job Edit buttons.
- Reusable `JobDetailDrawer` and `JobEditDrawer` exist under
  `apps/frontend/src/features/jobs-v2/components/` and are already imported
  cross-feature (e.g. `WorkspaceHeader` already imports `RecommendationBadge`
  from `@/features/jobs-v2/components`).

## Implementation steps

1. **Duplicate link → application** (`JobsPage.tsx`):
   - Change the duplicate `errorLink` to point at the existing job's
     application page and relabel it:
     `{ label: 'Open application', href: '/jobs/{id}/application' }`.
   - Do NOT save any note to the job's notes (backend already discards; leave
     `create_job` untouched).
2. **Job Detail + Job Edit buttons** on the application workspace:
   - `WorkspaceHeader.tsx`: add optional `onViewDetails` / `onEdit` props and
     render `Job Detail` / `Job Edit` buttons in the header's top-right action
     group (next to "Open job posting").
   - `ApplicationWorkspace.tsx`: hold local `detailOpen` / `editOpen` state,
     pass handlers into `WorkspaceHeader`, and render `JobDetailDrawer` /
     `JobEditDrawer` at the end of the layout (driven by those states).

## Testing requirements

- Backend: no backend change; existing `test_create_job.py` already asserts the
  duplicate returns 409 with `details.job_id` and that notes are not persisted
  as new data (the duplicate path never calls `create_job`). No new backend
  test needed.
- Frontend (vitest):
  - `JobsPage.test.tsx`: add a test that a duplicate create (fetch rejects with
    `JOB_ALREADY_EXISTS` + `details.job_id`) yields an `errorLink` anchor to
    `/jobs/{id}/application` labelled "Open application".
  - `ApplicationWorkspace.test.tsx`: assert the header renders `Job Detail` and
    `Job Edit` buttons and that clicking them opens the respective drawers.
- Run: `cd apps/frontend && npx vitest run` for affected files, plus
  `npm run lint` / `npm run typecheck` for the touched files.

## Constraints

- Do not change the backend; the user explicitly wants no new note persisted.
- Follow AGENTS.md: implementation-history first (this file), docs/tests before
  code. UX changes must update `docs/ux/features/applications/workspace.md`
  (and the `docs/ux/DESIGN.md` application-workspace wireframe) with ASCII
  wireframes reflecting the new buttons and the duplicate-link behavior.
