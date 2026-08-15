# Prompt 153 - Recruiter companies list client jobs like production companies

## Objective

Make recruiting companies behave like production companies in the Company list
and detail drawer: they reference jobs in the list's Jobs column and get a
jobs listing in their detail drawer. The only difference is the jobs they
reference belong to other companies (client jobs they publish for), not their
own hiring.

## Current State

- The list Jobs column already adapts per type: `CompanyRow.tsx:34` shows
  `recruiter_job_count` ("listed for clients") for recruiters and `job_count`
  otherwise. This is correct and stays unchanged.
- The detail drawer header badge is already adaptive (`CompanyDetailDrawer.tsx`
  "N listed" vs "N jobs").
- The detail drawer currently shows recruiters a grouped **Recruiter for**
  section (`CompanyDetailDrawer.tsx`, removed in this change) fed by
  `recruiter_for`, whose jobs carry only `{ id, title, location }` — unlike the
  production-company **Linked Jobs** section (`CompanyJobsTab`) which shows
  role, location and Fit/Success/Overall scores.
- `_build_company_detail` (`companies_v2_router.py`) builds `recruiter_for`
  from `job_repo.get_by_ids(all_job_ids)`, which returns only
  `{ id, title, location }`.

## Changes

- `apps/backend/jobs/domain/repositories/job_repository.py` + `sa_job_repository.py`:
  add `get_jobs_by_ids(job_ids)` returning full `job_model_to_dict` dicts (role,
  location, match, score, fit/success/overall).
- `apps/backend/companies/presentation/api/schemas/companies_v2.py`: add
  `recruiter_jobs: list[CompanyJobRefSchema]` to `CompanyDetailResponseSchema`.
- `apps/backend/companies/presentation/api/companies_v2_router.py`
  `_build_company_detail`: fetch full job data via `get_jobs_by_ids`, build a
  flat, role-sorted `recruiter_jobs` list and include it in the response.
- `apps/frontend/src/entities/company/types.ts`: add
  `recruiter_jobs?: CompanyLinkedJob[]` to `CompanyDetail`.
- `apps/frontend/src/features/companies-v2/components/CompanyDetailDrawer.tsx`:
  replace the grouped "Recruiter for" section with a **Jobs listed for clients**
  section rendered through the existing `CompanyJobsTab` fed by
  `recruiter_jobs` (role, location, scores, open-in-drawer). Remove the now
  redundant grouped listing.

## Testing Requirements

- Backend: extend `test_detail_exposes_recruiter_for_and_count` in
  `apps/backend/tests/companies/presentation/api/test_companies_v2_api.py` to
  assert `recruiter_jobs` (ids/roles). Add `TestGetJobsByIds` in
  `apps/backend/tests/jobs/infrastructure/repositories/test_sa_job_repository_extra.py`.
- Frontend: rewrite the recruiter block in
  `apps/frontend/src/features/companies-v2/components/CompanyDetailDrawer.test.tsx`
  to assert the flat "Jobs listed for clients" listing and open-in-drawer.
- Run:
  `uv run pytest apps/backend/tests/companies/presentation/api/test_companies_v2_api.py apps/backend/tests/jobs/infrastructure/repositories/ -q`
  and `cd apps/frontend && npx vitest run`.

## Constraints

- No cross-context FK / raw SQL (AGENTS.md rules 14–15). The flat job refs are
  logical projections only.
- Respect AGENTS.md rules 13 (UX doc + wireframe updates), 2 (implementation
  history before code), 10 (no routes in `entrypoints/api.py`).
