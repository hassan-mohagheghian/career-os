# Prompt 166 - Fine-Grained Job Rank Using All Scores

## Objective

Refine the job rank (added in prompt 165) so it is **fine-grained**: instead of
ranking by overall score alone (ties share a rank), sort jobs by **overall,
then success, then fit**, and break the final all-equal tie by `id` (desc, the
same tiebreak the list uses). Each non-deleted job gets a unique, deterministic
rank matching its position in the list sorted that way.

## Current State

- `IJobRepository.overall_score_rank(job_id)` /
  `SQLAlchemyJobRepository.overall_score_rank` ranks by `overall_score` alone
  with competition ranking (`apps/backend/jobs/infrastructure/repositories/sa_job_repository.py:812`).
- Called 3× in `jobs_v2_router.py` (521, 595, 629) and returned as `rank` on
  `JobDetailResponseSchema`.
- Docs describe rank as "jobs with the same overall score share a rank"
  (`docs/api/API.md`, `docs/ux/features/jobs/page.md`, `docs/ux/DESIGN.md`,
  `docs/ux/features/applications/workspace.md`).

## Changes

- Rename the method to `score_rank(job_id)` in `IJobRepository` and the
  SQLAlchemy implementation, and update the 3 router call sites.
- Implement rank = `1 + count(non-deleted jobs strictly before this job)` in the
  ordering `(overall desc, success desc, fit desc, id desc)` with NULLS LAST.
  Use a `-1` sentinel via `func.coalesce` for NULL scores (scores are 0–100, so
  `-1` sorts last, matching NULLS LAST). Break the final all-three-equal tie by
  `id > job_id` so ranks are unique.

## Testing Requirements

- `test_sa_job_repository_extra.py`: rename `TestOverallScoreRank` →
  `TestScoreRank`; keep the simple cases, update the tie case (equal scores now
  break by id desc), and add cases proving success then fit break ties:
  - same overall, higher success ranks above;
  - same overall + success, higher fit ranks above;
  - same overall + success + fit → id desc decides;
  - NULL scores sort last after all scored jobs.
- `test_jobs_v2_api.py`: `TestJobRankV2API` — add a case where two jobs share
  overall but differ in success, asserting the higher-success job ranks first.
- Run `uv run pytest apps/backend/tests/jobs/ -v`.

## Constraints

- Rank stays derived (no migration, no stored column), single job context
  (AGENTS.md rule 15).
- Preserve NULLS LAST semantics consistent with the list sort
  (`search_jobs_cursor`).
- Docs-first: update the rank wording in `docs/api/API.md` and the three UX
  docs before coding.
