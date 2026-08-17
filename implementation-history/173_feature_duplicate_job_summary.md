# Prompt 173 - Duplicate Job Error Summary + Job Detail Link

## Objective

When the Add Job drawer returns a **duplicate** error, show a compact summary of
the already-existing job below the error message — the same top-of-detail block
used by the job detail drawer (GradeBadge + Overall/Success/Fit score cards +
RankBadge + title + identity rows) — plus a link to open the full job detail
drawer. The existing "Open application" error link stays.

## Current State

- Backend `create_job` (`jobs/presentation/api/jobs_v2_router.py:101`) calls
  `find_duplicate_job(repo, url)` (`jobs/domain/services/job_url_rules.py:69`)
  and, on a hit, raises `JobAlreadyExistsError(job_id=...)`
  (`shared/application/exceptions.py:49`). The error handler
  (`shared/presentation/error_handler.py`) serializes `exc.details` verbatim, so
  the payload is currently only `{"job_id": ...}`.
- Job detail header (`jobs-v2/components/JobDetailDrawer.tsx:486`) composes
  GradeBadge, `JobScoreCard` (Overall/Success/Fit), `RankBadge`, title, and a
  two-column grid of `DetailRow`s. `JobScoreCard`/`DetailRow` are local to that
  file. Rank comes from `repo.score_rank(id)`, company type from
  `_linked_company_type(job_dict, company_repo)`, tracking status from
  `application_repo.statuses_by_job_ids([id])`.
- Frontend: `useCreateJob` (`hooks/useCreateJob.ts`) parses only
  `error.details.job_id`; `JobsPage` passes `error` + `errorLink` (→
  `/jobs/:id/application`) into `CreateEntityDrawer`, which renders a simple
  error row. No summary payload flows through today.

## Changes

### Backend

- `shared/application/exceptions.py` — extend `JobAlreadyExistsError.__init__` to
  accept `job: dict | None`; merge `{"job_id": ...}` and `{"job": {...}}` into
  `details`.
- `jobs/presentation/api/jobs_v2_router.py`:
  - Add `company_repo` and `application_repo` dependencies to `create_job`.
  - On duplicate, build the summary via a new `_job_summary(job, rank,
    company_type, tracking_status)` helper (mirrors `_job_detail_payload`
    fields: title/company/company_type/location/visa/salary/employment/work
    types/scores/rank/tracking_status/url) and pass it to
    `JobAlreadyExistsError`.
  - `_job_summary` reuses `_parse_string_list` for array columns.

### Frontend

- `entities/job/types.ts` — add `JobSummary` interface (id, title, company,
  company_id, company_type, location, visa, salary, employment_types,
  work_types, overall/fit/success_score, rank, tracking_status, url,
  updated_at).
- `features/jobs-v2/hooks/useCreateJob.ts` — parse `error.details.job` into a
  new `existingJob` state (in addition to `existingJobId`); reset it in
  `clearError` and on new submit; return it.
- `features/jobs-v2/components/JobsPage.tsx` — pass `existingJob` and
  `onViewJobDetails={(id) => onDetailJobIdChange(id)}` into `CreateEntityDrawer`.
- `shared/components/CreateEntityDrawer.tsx`:
  - Add props `existingJob?: JobSummary | null` and `onViewJobDetails?`.
  - Add local `JobScoreCard`/`SummaryRow` (mirrors job detail) and a
    `JobSummaryCard` that renders GradeBadge + score cards + RankBadge + "Open
    job posting" link + title + two-column detail rows (Company, Type, Location,
    Visa, Tracking, Employment, Salary, Work Types) + "View full job details"
    button wired to `onViewJobDetails`.
  - Render `JobSummaryCard` below the error row when `existingJob` is present.

## Testing

- Backend: extend `test_create_duplicate_linkedin_job_returns_409` to assert
  `error.details.job.id` equals the first job id.
- Frontend: `CreateEntityDrawer.test.tsx` — render summary (title/company/
  location/scores/rank/Open job posting href); `onViewJobDetails` fires on
  "View full job details". `useCreateJob.test.tsx` — parses `details.job` into
  `existingJob`.
- Typecheck the changed frontend files; no new ruff errors.

## Constraints

- No FKs across contexts; keep `JobSummary` a plain logical payload.
- No new API route in `entrypoints/api.py` (per-context router).
- Follow rule 13: document the UI change with an ASCII wireframe under
  `docs/ux/features/` and update the index.
