# Prompt 165 - Job Overall-Score Rank

## Objective

Give every job a **rank number** representing its position in the full job list
when sorted by **overall score** (descending). Expose that rank on the job
detail API and render it in the **Job Detail drawer** and the **Job Application
workspace header**.

## Current State

- The job list is sorted by `overall_score` desc with a NULLS LAST policy
  (`apps/backend/jobs/infrastructure/repositories/sa_job_repository.py`,
  `search_jobs_cursor`).
- `GET /api/jobs/{job_id}` returns `JobDetailResponseSchema`
  (`apps/backend/jobs/presentation/api/schemas/jobs_v2.py:224`) with a `scores`
  block but no rank.
- The Job Detail drawer renders the score strip at
  `apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.tsx:487` (GradeBadge
  + Fit / Success / Overall `JobScoreCard`s).
- The Application workspace header renders the same score cards at
  `apps/frontend/src/features/job-application/components/WorkspaceHeader.tsx:108`.
- Both frontend views read `JobDetail` from `apps/frontend/src/entities/job/types.ts:226`.

## Changes

**Backend — repository** (`sa_job_repository.py` + `job_repository.py`):
- Add `overall_score_rank(job_id: str) -> int | None` to `IJobRepository` and
  implement in `SQLAlchemyJobRepository`. Competition ranking over non-deleted
  jobs: rank = `1 + count(overall_score > X)`; for a NULL score the job ties at
  the end (rank = `1 + count(overall_score IS NOT NULL)`), matching the list's
  NULLS LAST order. Returns `None` when the job does not exist.

**Backend — API** (`jobs_v2_router.py` + `schemas/jobs_v2.py`):
- Add `rank: int | None = None` to `JobDetailResponseSchema`.
- Compute `rank = repo.overall_score_rank(job_id)` in `get_job_detail` (inline
  response) and pass `rank` through `_job_detail_payload` for `update_job` and
  `set_job_company` (all three already hold `repo`).

**Frontend**:
- `types.ts`: add `rank: number | null` to `JobDetail`.
- Add `RankBadge` (`apps/frontend/src/shared/components/RankBadge.tsx`) — value
  `#N` above a "Rank" label, consistent with the existing score cards; renders
  nothing when `rank == null`.
- `JobDetailDrawer.tsx`: render `<RankBadge rank={detail.rank ?? null} />` in the
  score strip (after Overall, before `[Why]`).
- `WorkspaceHeader.tsx`: render `<RankBadge rank={job.rank ?? null} />` in the
  right-side score group (after the GradeBadge / score cards).

## Testing Requirements

- `apps/backend/tests/jobs/infrastructure/repositories/test_sa_job_repository_extra.py`:
  new `TestOverallScoreRank` — top score rank 1, ties share a rank, NULL-score
  job ranks after all scored jobs, deleted jobs excluded, missing job returns `None`.
- `apps/backend/tests/jobs/presentation/api/test_jobs_v2_api.py`: assert
  `GET /api/jobs/{id}` returns `rank` (top job rank 1; second-ranked job rank 2).
- `apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.test.tsx`: add
  `rank` to `sampleDetail` and assert the rank is rendered.
- `apps/frontend/src/features/job-application/components/ApplicationWorkspace.test.tsx`:
  assert the header renders the rank.
- Run: `uv run pytest apps/backend/tests/jobs/ -v`,
  `cd apps/frontend && npx vitest run` + `npm run lint` + `npm run typecheck`.

## Constraints

- Respect AGENTS.md rule 15: rank is computed via the job repository (single
  context) — no cross-context FK.
- No DB migration needed (rank is derived, not stored).
- Rank is a **global** ordering independent of list filters; ties share a rank
  (competition ranking). NULLS (unscored jobs) tie at the end, matching the
  existing list sort.
- Docs-first: update `docs/api/API.md` (job detail JSON gains `rank`) and the UX
  docs `docs/ux/features/jobs/page.md` (drawer layout) + 
  `docs/ux/features/applications/workspace.md` (header wireframe) with ASCII
  wireframes before coding.
