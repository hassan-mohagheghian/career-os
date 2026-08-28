# Prompt 194 - Feature: multi-select tracking & recommendation filters on Jobs list

## Objective

Make the **Tracking** and **Recommendation** filters in the Jobs list toolbar
multi-select (OR semantics) instead of single-select dropdowns. A user must be
able to filter, e.g., "Applied OR Interview" or "Apply OR Consider".

## Current State

- `apps/frontend/src/features/jobs-v2/components/JobsToolbar.tsx` renders both
  filters as shadcn/ui `Select` (single value). The tracking `Select` only
  exposed 7 of the 10 valid `TRACKING_STATUSES` (`seen`/`preparing`/
  `ready_to_apply` were missing from the dropdown, though valid backend values).
- Filter state in `useJobsInfiniteQuery.ts` is `useState<RecommendationFilter>('')`
  / `useState<TrackingStatusFilter>('')` (single string, `''` = all).
- API client (`entities/job/api.ts`) serializes a single query param.
- Backend `jobs_v2_router.py` parses `recommendation` (single, regex-validated)
  and `tracking_status` (single). `tracking_status` is resolved in the router
  into `job_ids`/`exclude_job_ids` via the `applications` context repository;
  `recommendation` is forwarded as a string to `ListJobsV2Request` →
  `sa_job_repository.search_jobs_cursor` which does an `==` SQL match.

## Implementation Steps

### Frontend
1. `entities/job/types.ts`: `RecommendationFilter = 'apply' | 'consider' | 'skip'`
   (drop `''`); `TrackingStatusFilter = TrackingStatus` (drop `''`);
   `JobSearchQuery.recommendation?: RecommendationFilter[]`,
   `tracking_status?: TrackingStatusFilter[]`.
2. `features/jobs-v2/components/MultiSelectFilter.tsx` (new): generic Popover +
   Checkbox multi-select (`label`, `options`, `selected: T[]`, `onChange: (T[])=>void`).
   Shows selected labels in the trigger + a count badge; Clear action.
3. `JobsToolbar.tsx`: type the two props as arrays; replace the two `Select`s
   with `<MultiSelectFilter>` for **all** recommendation values and **all 10**
   tracking statuses (fixes the missing 3). Update `JobsToolbarProps`.
4. `useJobsInfiniteQuery.ts`: state becomes `RecommendationFilter[]` /
   `TrackingStatusFilter[]`; `filterKey` sends the array (omitted when empty);
   `activeFilterCount` counts each dimension when non-empty; `clearFilters`
   resets to `[]`; setters typed accordingly. Remove `''` comparisons.
5. `JobsPage.tsx`: update the two prop types to arrays (pass-through).
6. `entities/job/api.ts`: serialize arrays via `params.append(..., v)` for each
   value (repeated query params).

### Backend
7. `jobs/presentation/api/jobs_v2_router.py`: accept `recommendation` and
   `tracking_status` as `list[str] | None = Query(None)`; normalize + validate
   each value against the allowed set (raise `422` on invalid). Resolve multiple
   tracking statuses with **OR** semantics: union of jobs whose application
   status matches any specific status, plus (if `not_applied` selected) jobs
   with no application (`repo.get_all_active()` minus applied ids). Intersect
   with any pre-existing `job_ids` (e.g. from processing-status).
8. `jobs/application/use_cases/list_jobs_v2.py`: `ListJobsV2Request.recommendation`
   becomes `list[str] | None`.
9. `jobs/domain/repositories/job_repository.py` + `sa_job_repository.py`:
   `search_jobs_cursor(recommendation: list[str] | None = None)`; SQL uses
   `JobAnalysisModel.recommendation.in_(recommendation)`.

### Tests
10. Frontend `JobsToolbar.test.tsx` + `useJobsInfiniteQuery.test.tsx`: drive the
    multi-select (arrays); assert `onChange(['apply'])`, `recommendation: ['apply']`,
    multi-value send, active-count, clear → `[]`.
11. Backend `test_jobs_v2_api.py`: existing single-value tests still pass; add
    multi-value recommendation + tracking (OR) tests (repeated params and
    comma form).

### Docs
12. `docs/ux/features/jobs/page.md`: update Toolbar controls table;
    rewrite `## Recommendation Filter` and add `## Tracking Filter` to describe
    multi-select OR behavior with an ASCII wireframe of the popover.

## Testing Requirements

- `cd apps/frontend && npx vitest run` (jobs-v2) pass; `npm run lint` + `npm run typecheck` clean.
- `uv run pytest apps/backend/tests/jobs/presentation/api/test_jobs_v2_api.py -v` pass.
- Manual: select two recommendations → only those jobs; select "Applied" +
  "Interview" → both; "not_applied" + "Applied" → union.

## Constraints

- No behavior change for other filters (processing/remote/visa/date remain
  single-select).
- Backward compatible: a single selected value behaves exactly as before
  (SQL `IN (value)` == `== value` for one element).
- Keep cross-context rule (no FK): tracking still resolves via the applications
  repository into `job_ids`; recommendation stays an SQL subquery.
- Follow repo rule 13: UX docs updated with wireframe.
