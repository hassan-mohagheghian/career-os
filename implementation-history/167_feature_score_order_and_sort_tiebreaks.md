# Prompt 167 - Score Display Order (Overall, Success, Fit) + Score Sort Tiebreaks

## Objective

1. **Display order**: Present score badges/cards left-to-right as **Overall, Success,
   Fit** (currently Fit, Success, Overall) in the job list row, job detail drawer, job
   application page header, company list row, company detail drawer header, and the
   company jobs tab. The grade badge stays first; the job `Rank` badge stays last (after
   Fit); the company `Why` button stays last.
2. **Sort tiebreaks** (backend only; frontend keeps sending the single primary sort
   field). Each score sort becomes multi-column, all columns NULLS LAST and sharing the
   chosen asc/desc direction:
   - `overall_score` sort → overall, success, fit
   - `fit_score` sort → fit, overall, success
   - `success_score` sort → success, overall, fit
   - Non-score sorts (`name`, `updated_at`, `created_at`) unchanged.

## Current State

- Display order is Fit → Success → Overall in `JobRow.tsx:96-99`,
  `JobDetailDrawer.tsx:487-507` (score strip + Rank), `WorkspaceHeader.tsx:108-117`
  (score strip + Rank), `CompanyRow.tsx:96-99`, `CompanyDetailDrawer.tsx:305-313`
  (score strip + Why), `CompanyJobsTab.tsx:46-51` (badges).
- Jobs list sort is SQL single-column in `sa_job_repository.py`
  (`search_jobs_cursor` keyset pagination, `search_jobs` offset pagination) using
  `sort_map` keyed by sort field; cursor format `value|id` with `__null__` sentinel.
- Companies list sort is Python single-key in `companies_v2_router.py`:
  `_score_value` (153), `_sort_key` (158), `SORTABLE_SCORE_FIELDS` (67),
  `SCORE_KEY_MAP` (70-72), applied at 245-248 (`with_value.sort(key=key,
  reverse=(order == "desc"))`, NULL primary → `without_value` tail).
- Rank (prompt 166) already uses overall, success, fit — no change here.
- Existing tests only assert single-column results on tied/null data, so they keep
  passing (verified for `test_sort_by_fit_score_nulls_last` and the jobs cursor tests).

## Changes

### Backend — jobs (`apps/backend/jobs/infrastructure/repositories/sa_job_repository.py`)
- Add `SCORE_SORT_COLUMNS` mapping sort field → `[JobModel.overall_score,
  JobModel.success_score, JobModel.fit_score]` per the tiebreak spec above; non-score
  sorts keep a single column.
- `search_jobs_cursor`: build ORDER BY over the multi-column list (each
  `.asc()/.desc().nulls_last()`, then `JobModel.id`). Generalize the keyset cursor to a
  tuple of boundary values: for multi-column score sorts encode `v1|v2|v3|id`; filter
  with `func.coalesce(col, sentinel)` lexicographic tuple comparison, sentinel `-1` for
  desc / large (e.g. 1000) for asc to keep NULLS LAST; final all-equal tie by `id`
  (`id < cur_id` desc, `id > cur_id` asc). Keep the existing single-column path for
  non-score sorts byte-for-byte.
- `search_jobs`: apply the same multi-column ORDER BY.

### Backend — companies (`apps/backend/companies/presentation/api/companies_v2_router.py`)
- Replace `_score_value`/`_sort_key` score branch with a multi-column tuple key:
  `_sort_key(row, sort, order)` returns `None` when the primary score is `None`
  (pushed to `without_value` tail), else a tuple of the tiebreak scores with `None`
  replaced by the direction sentinel (`-1` desc / `1000` asc). Update the call sites at
  245-248 to pass `order` and keep `reverse=(order == "desc")` (reversing a tuple
  reverses all columns consistently).

### Frontend — display order (Overall, Success, Fit)
- `JobRow.tsx`, `JobDetailDrawer.tsx`, `WorkspaceHeader.tsx`, `CompanyRow.tsx`,
  `CompanyDetailDrawer.tsx`, `CompanyJobsTab.tsx`: reorder score badges/cards to
  Overall, Success, Fit. Grade badge stays first; `Rank` badge stays after Fit (jobs);
  `Why` stays after Fit (company detail).

## Testing Requirements (TDD red first)

- Jobs repo tests (`test_sa_job_repository_extra.py`): add cases proving the cursor
  list ties on `overall` break by `success` then `fit` then `id` across page boundaries
  (desc and asc), and that a `fit_score`/`success_score` sort uses its own tiebreak.
- Companies API tests (`test_companies_v2_api.py`): add a case with tied primary scores
  and differing secondary scores proving the tuple tiebreak order for
  `overall_score`, `fit_score`, `success_score` (desc + asc), NULL secondary last.
- Frontend tests: assert badge/card order is Overall → Success → Fit in the six
  components (extend existing score tests to check ordering, e.g. via container
  textContent position or `toHaveTextContent` order). Existing tests already render all
  three values; extend them to assert order.
- Run `uv run pytest apps/backend/tests/jobs/ -v`, the companies API tests, and
  `cd apps/frontend && npx vitest run`.

## Constraints

- Score sorts are single bounded context each (jobs schema / companies schema) — no
  cross-context FKs (AGENTS.md rule 15).
- Do not change the frontend sort request; only the backend applies the tiebreak.
- Keep the legacy single-column cursor path for non-score sorts unchanged to avoid
  breaking existing cursor format/tests.
- Docs-first: update score-order wording and add the sort-tiebreak tables in the UX and
  API docs before coding.
