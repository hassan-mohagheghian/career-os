# Prompt 168 - Job Rank in the Job List

## Objective

Surface each job's rank in the **job list** rows and unify rank across the list,
detail drawer and application page. Rank uses **competition ranking (`RANK()`)**:
computed over the full non-deleted job list sorted by **overall, then success,
then fit** score (each descending, NULLS LAST); jobs with identical scores share
a rank and the next distinct rank skips. It is an absolute position independent
of the list's current sort/filter, identical everywhere.

## Current State

- `score_rank(job_id)` computes a single job's rank with **2 queries per call**
  (`sa_job_repository.py:877`). Used 3× in `jobs_v2_router.py` (521, 595, 629)
  for the detail/application routes. This must **not** be looped per list row
  (N+1 → 50–200 queries per page).
- `list_jobs_v2` (`jobs_v2_router.py:227`) returns `JobListItemSchema` items via
  `_v2_job_to_schema` (185); schema at `schemas/jobs_v2.py:90` has no `rank`.
- Frontend `JobRow.tsx` shows grade + O/S/F `ScoreBadge`s; `RankBadge` exists and
  is used in `JobDetailDrawer.tsx` / `WorkspaceHeader.tsx`.
- Codebase precedent for Postgres window functions:
  `sa_processing_execution_repository.py:173` (`func.row_number().over(...)`).

## Changes

### Backend — repo (`sa_job_repository.py` + `job_repository.py`)
- Add `ranks_by_ids(job_ids: list[str]) -> dict[str, int]` to `IJobRepository`
  and the SQLAlchemy implementation: **one** query computing
  `func.rank().over(order_by=[coalesce(overall_score,-1) desc,
  coalesce(success_score,-1) desc, coalesce(fit_score,-1) desc])` — **no `id`
  tiebreak**, so equal-score jobs share a rank (competition ranking). The window
  is computed in a subquery over the **full** non-deleted set (so ranks are
  absolute, independent of the requested subset), then filtered to `job_ids`.
- Replace the per-job `score_rank` implementation so it delegates to
  `ranks_by_ids([job_id]).get(job_id)` — the drawer and application page now use
  the exact same `RANK()` window as the list (previously it was a unique
  `ROW_NUMBER`-style rank with an `id` tiebreak).

### Backend — API (`jobs_v2_router.py`)
- In `list_jobs_v2` after `page_job_ids` (285): `ranks = repo.ranks_by_ids(
  page_job_ids)` once; pass `ranks.get(job_id)` into `_v2_job_to_schema`.

### Backend — schema (`schemas/jobs_v2.py`)
- Add `rank: int | None = None` to `JobListItemSchema`; thread through
  `_v2_job_to_schema`.

### Frontend
- `JobRow.tsx`: render `RankBadge` (imported from the shared UI) after the Fit
  `ScoreBadge`. Keep it display-only like the detail drawer.
- `entities/job/types.ts`: add `rank?: number | null` to the list item type.

## Testing Requirements (TDD red first)

- Repo (`test_sa_job_repository_extra.py`): `TestRanksByIds` — competition
  ranking: distinct-score jobs rank 1,2,3; jobs with identical (overall, success,
  fit) scores **share** a rank (all `RANK()`), NULLS LAST (unscored last), only
  the requested ids, excludes deleted jobs, ranks absolute over the full set.
  `TestScoreRank` — update the all-equal tie case to expect a **shared** rank
  (competition ranking), and confirm `score_rank` matches the list.
- API (`test_jobs_v2_api.py`): list items carry `rank`, and it is 1-based over
  the full set (not just the page).
- Frontend (`JobRow.test.tsx`): renders the rank badge when present, hides it
  when absent.
- Run `uv run pytest apps/backend/tests/jobs/ -v` and
  `cd apps/frontend && npx vitest run`.

## Constraints

- Low cost: exactly **one** query per list request (no per-row `score_rank`);
  `score_rank` reuses the same window for a single job.
- Rank uses competition ranking (`RANK()`) everywhere — list, drawer, application
  page — so all three always agree.
- Rank is absolute over the full non-deleted job set (independent of sort/filter).
- Docs-first (AGENTS.md rule 13): update `docs/api/jobs/list-jobs.md`,
  `docs/api/API.md`, `docs/ux/features/jobs/page.md`, `docs/ux/features/jobs/job-row.md`,
  `docs/ux/features/applications/workspace.md`, `docs/ux/DESIGN.md` before coding.