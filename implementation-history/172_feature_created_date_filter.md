# Prompt 172 - Created-At Date Filter for Jobs

## Objective

Add a **created-at date filter** to the Jobs list, with four presets:
**Today**, **Yesterday**, **Last Week**, **Last Month** (plus "All"). The filter
is a single dropdown in `JobsToolbar` alongside the existing Status / Location /
Remote / Visa / Recommendation / Tracking filters, applied server-side in
`search_jobs_cursor` against `jobs.created_at`.

## Current State

- Backend v2 list flow: `jobs_v2_router.list_jobs_v2`
  (`jobs/presentation/api/jobs_v2_router.py:228`) builds a `ListJobsV2Request`
  (`jobs/application/use_cases/list_jobs_v2.py`) that the use case passes to
  `SQLAlchemyJobRepository.search_jobs_cursor`
  (`jobs/infrastructure/repositories/sa_job_repository.py:603`). Filters already
  supported: query, company_id, location, remote, visa, score min/max, pinned,
  recommendation. `recommendation` uses `Query(pattern="^(apply|consider|skip)$")`
  as the constrained-enum example.
- `JobModel.created_at` is a `Text` column storing ISO UTC strings
  (`default=datetime.utcnow`). Existing sort on `created_at` compares the string
  directly, so an ISO string range compare (`>=` / `<`) is consistent with the
  existing approach.
- Frontend: `JobsToolbar.tsx` renders filter `Select`s driven by state in
  `useJobsInfiniteQuery.ts`, which serializes the `filterKey` into
  `jobApi.searchInfinite` (`entities/job/api.ts`). `JobSearchQuery` lives in
  `entities/job/types.ts` with `RecommendationFilter`/`TrackingStatusFilter` as
  the established union-`''` filter types. `JobsPage.tsx` and the widget
  `widgets/jobs-page-v2/index.tsx` thread the toolbar props.

## Changes

### Backend — `jobs/application/use_cases/list_jobs_v2.py`

- Add `created_date: str | None = None` to `ListJobsV2Request`.
- Pass `created_date=request.created_date` to `search_jobs_cursor`.

### Backend — `jobs/infrastructure/repositories/sa_job_repository.py`

- Add `created_date: str | None = None` to `search_jobs_cursor` signature.
- Add a private helper `_created_date_range(key) -> tuple[str | None, str | None]`
  returning `(start_iso, end_iso)` computed with `datetime.utcnow()`:
  - `today` → `(today 00:00:00, None)`
  - `yesterday` → `(yesterday 00:00:00, today 00:00:00)`
  - `week` → `(now - 7 days, None)`
  - `month` → `(now - 30 days, None)`
- When `created_date` is set, apply `JobModel.created_at >= start` (and
  `JobModel.created_at < end` for `yesterday`). Unknown key → no filter.

### Backend — `jobs/presentation/api/jobs_v2_router.py`

- Add `created_date: str | None = Query(None, pattern="^(today|yesterday|week|month)$")`
  and pass it into the request.

### Frontend — `entities/job/types.ts`

- Add `export type CreatedDateFilter = 'today' | 'yesterday' | 'week' | 'month' | ''`
  and `created_date?: CreatedDateFilter` on `JobSearchQuery`.

### Frontend — `entities/job/api.ts`

- In `search` and `searchInfinite`, `if (query.created_date) params.set('created_date', query.created_date)`.

### Frontend — `features/jobs-v2/hooks/useJobsInfiniteQuery.ts`

- Add `filterCreatedDate` state + setter, include it in `filterKey`,
  `activeFilterCount`, `clearFilters`, and pass `created_date` to `searchInfinite`.

### Frontend — `features/jobs-v2/components/JobsToolbar.tsx`

- Add `filterCreatedDate` / `onFilterCreatedDateChange` props and a `Select`
  (labels: All / Today / Yesterday / Last Week / Last Month) consistent with the
  existing filter selects.

### Frontend — `features/jobs-v2/components/JobsPage.tsx` + `widgets/jobs-page-v2/index.tsx`

- Thread `filterCreatedDate` / `onFilterCreatedDateChange` props through.

## Testing

- Backend: add `created_date` cases to
  `tests/jobs/infrastructure/repositories/test_sa_job_repository_extra.py`
  (today / yesterday / week / month bound correctness) and a router test asserting
  the query param is accepted; run `uv run pytest apps/backend/tests/jobs/`.
- Frontend: add a toolbar test that the Date select renders the options and that
  selecting one calls `onFilterCreatedDateChange`; add a query-hook test asserting
  `created_date` appears in the request; run `npx vitest run` and `npm run typecheck`.

## Constraints

- AGENTS.md rule 13: document the new filter in
  `docs/ux/features/jobs/page.md` (and the jobs toolbar layout) plus
  `docs/api/jobs/list-jobs.md` / `docs/api/API.md`.
- No schema change, no migration.
- Default (no filter) shows all jobs; clear-filters resets the date filter.
