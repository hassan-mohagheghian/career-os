# Prompt 154 - Fix recruiter jobs with unknown hiring company

## Objective

A recruiter company's job count and "Jobs listed for clients" listing were
omitting jobs the recruiter published when the hiring company is unknown. Fix
the count/list semantics so a `role="recruiter"` association is enough — only
jobs where the recruiter is also the hiring company are excluded.

## Current State

- `sa_job_company_repository.py` `recruiter_job_counts` and `recruiter_hiring_pairs`
  only counted a recruiter's job when the job also had a `role="hiring"` row for
  a different company. A job published by a recruiter with no known hiring
  company (e.g. `01a003ce-6e8f-73c6-a990-84c2925de178` published by A2G
  Consulting BV) was therefore excluded from the list's Jobs column and the
  detail drawer's `recruiter_jobs`.
- `companies_v2_router.py::_build_company_detail` derived `recruiter_jobs` from
  `recruiter_hiring_pairs`, so jobs without a hiring company never appeared.
- The old behavior was codified in
  `test_sa_job_company_repository.py::test_excludes_jobs_without_distinct_hiring_company`.

## Changes

- `apps/backend/jobs/infrastructure/repositories/sa_job_company_repository.py`:
  `recruiter_job_counts` now counts every job where the company is
  `role="recruiter"`, excluding only jobs where the same company also has a
  `role="hiring"` row (self-hiring). It no longer requires a distinct hiring
  company.
- `apps/backend/companies/presentation/api/companies_v2_router.py`
  `_build_company_detail`: build `recruiter_jobs` from
  `list_by_company(id, role="recruiter")` minus self-hiring job ids, fetch full
  job data via `get_jobs_by_ids`, and set `recruiter_job_count = len(recruiter_jobs)`.

## Testing Requirements

- Update
  `apps/backend/tests/jobs/infrastructure/repositories/test_sa_job_company_repository.py`
  (rename/extend the exclusion test to expect the no-hiring-company job to count).
- Add
  `apps/backend/tests/companies/presentation/api/test_companies_v2_api.py::test_detail_lists_recruiter_jobs_without_known_hiring_company`.
- Run:
  `uv run pytest apps/backend/tests/jobs/infrastructure/repositories/test_sa_job_company_repository.py apps/backend/tests/companies/presentation/api/test_companies_v2_api.py -q`.

## Constraints

- `recruiter_hiring_pairs` (→ `recruiter_for`) stays as-is: it maps to known
  hiring companies, so it still requires a hiring row.
- No schema/migration change; no cross-context FK or raw SQL (AGENTS.md 14–15).
