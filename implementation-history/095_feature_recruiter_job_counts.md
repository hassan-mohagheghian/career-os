# Prompt 095 - Surface Recruiter Job Counts in Company List and Drawer

## Objective

Show the number of jobs a company **lists** (publishes for clients) for
recruiter-type companies (`RECRUITING_AGENCY` / `STAFFING_COMPANY`) in the
company list's Jobs column and in the company detail drawer's header badge.
Product companies keep showing `job_count` (jobs they hire for) as today.

## Current State

- `GET /api/companies/list` returns `job_count` per company = non-deleted jobs
  whose `company_id` is this company (the **hiring** count). For recruiters
  this is ~0, so the list row's Jobs column shows `—`.
- The company detail drawer (3.9.0) already exposes `recruiter_job_count` +
  `recruiter_for` (per-client breakdown) and renders a "Recruiter for N jobs"
  section, but the header badge still shows `job_count` (0 for recruiters).
- `SQLAlchemyJobCompanyRepository.recruiter_hiring_pairs` computes the detail
  semantics: recruiter jobs that have an attributed **distinct** hiring
  company (excludes self-referencing and jobs without a hiring row).

## Design Decisions (confirmed with user)

1. **Adaptive single column**: the existing Jobs column shows
   `recruiter_job_count` for recruiter-type companies and `job_count` for all
   others; a tooltip clarifies "N listed for clients" for recruiters.
2. **Adaptive header badge**: the drawer's "N jobs" header badge shows
   `recruiter_job_count` for recruiter-type companies (else `job_count`). The
   "Recruiter for N jobs" section with per-client breakdown stays.

## Implementation Steps

1. **Backend**:
   - Add `recruiter_job_counts(company_ids)` to `IJobCompanyRepository` /
     `SQLAlchemyJobCompanyRepository`: one aggregate query over `job_companies`
     (role=`recruiter` with an attributed distinct hiring company), grouped by
     company_id — mirrors `recruiter_hiring_pairs` semantics.
   - Add `recruiter_job_count: int = 0` to `CompanyListItemSchema`.
   - Wire `get_job_company_repo` into `list_companies_v2`, compute counts for
     the current page, and pass into `_to_list_item`.
2. **Frontend**:
   - Add `recruiter_job_count` to `CompanyListItem`.
   - `CompanyRow`: Jobs column shows `recruiter_job_count` for recruiter-type
     companies (else `job_count`), with a `title` tooltip.
   - `CompanyDetailDrawer`: header badge adapts to `recruiter_job_count` for
     recruiter-type companies; keep the "Recruiter for" section.
3. **Tests**:
   - Backend: list API test that a recruiter company exposes
     `recruiter_job_count` while a product company exposes `job_count`.
   - Frontend: CompanyRow Jobs-column test and CompanyDetailDrawer header badge
     test for recruiter-type companies.
4. **Docs**: `docs/ux/features/companies/page.md` (Jobs column),
   `docs/ux/features/companies/company-detail.md` (header badge),
   `docs/api/companies/list-companies.md`, `DESIGN.md` wireframes.

## Testing Requirements

- `uv run pytest apps/backend/tests/ -q` green.
- `cd apps/frontend && npx vitest run` green (typecheck/lint pre-existing
  failures untouched).

## Constraints

- Reuse the detail `recruiter_job_count` semantics (distinct attributed hiring
  company, self excluded) so list and drawer never disagree.
- Do not add API routes to `entrypoints/api.py`; use per-context routers.
- AGENTS.md rule 13: UX wireframes must be updated.
