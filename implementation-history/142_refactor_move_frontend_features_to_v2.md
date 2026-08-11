# Prompt 142 - Move frontend job/company features to v2 slices

## Objective

Finish the frontend half of the legacy-removal: the last components still
living under `features/jobs/` and `features/companies/` move into the v2
feature slices (`features/jobs-v2/`, `features/companies-v2/`), and the legacy
feature directories are deleted.

## Current State

- `apps/frontend/src/features/jobs/hooks/useCreateJob.ts` (+ test) — the only
  legacy jobs file; JobsPage still imports it via
  `@/features/jobs/hooks/useCreateJob`.
- `apps/frontend/src/features/companies/components/CompanyJobsTab.tsx` (+ test)
  and `CompanyNotesTab.tsx` (+ test) — imported by the v2 company drawers.
- `entities/job/api.ts` has no `create` method (raw `fetch('/api/jobs')` lives
  in the legacy hook); `entities/company/api.ts` has no notes/links methods
  (raw `fetch('/api/companies/...')` lives in CompanyNotesTab).

## Changes

- Add `jobApi.create` + `CreateJobRequest` / `CreateJobResponse` types to
  `entities/job/api.ts`.
- Move `useCreateJob` to `features/jobs-v2/hooks/useCreateJob.ts`, refactor it
  to call `jobApi.create`, and extract the duplicate-job `existingJobId` from
  `ApiError.body.error.details.job_id`.
- Extend `shared/api/http-client` so `ApiError` carries the parsed response
  `body` (needed for the duplicate-job id).
- Add `listNotes` / `addNote` / `updateNote` / `deleteNote` / `addLink` /
  `updateLink` / `deleteLink` to `entities/company/api.ts`.
- Move `CompanyJobsTab` + `CompanyNotesTab` to
  `features/companies-v2/components/` and refactor `CompanyNotesTab` to use
  `companyApi`.
- Update imports in `JobsPage.tsx`, `CompanyDetailDrawer.tsx`,
  `CompanyEditDrawer.tsx`.
- Delete `features/jobs/` and `features/companies/`.

## Testing Requirements

- Rewrite `useCreateJob.test.tsx` (mocks `jobApi.create`), `CompanyNotesTab
  .test.tsx` (mocks `companyApi`), keep `CompanyJobsTab.test.tsx` behavior.
- Extend `http-client.test.ts` for `ApiError.body`.
- Run `npx vitest run` and `npm run typecheck`.

## Constraints

- Preserve hook/component public props and behavior — no UX change.
- FSD boundaries: hooks under `features/*/hooks`, components under
  `features/*/components`, HTTP via the entity `api.ts` modules only.
