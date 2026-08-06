# Prompt 096 - Link "Recruiter for N Jobs" Rows to the Actual Jobs

## Objective

The "Recruiter for N jobs" section in the company detail drawer currently
links each row to the hiring **company** (a company detail drawer), even though
the row's count is about **jobs**. Change the section so each hiring company's
jobs are reachable: expose the underlying job ids/titles in the detail API and
render per-job links that open the job detail drawer (`/jobs?job=<id>`), with
the hiring company link kept as a secondary reference.

## Current State

- `GET /api/companies/list/{id}` detail payload includes
  `recruiter_job_count` + `recruiter_for` where each `recruiter_for` entry is
  `{company_id, name, job_count}` (per-client aggregation, 094).
- `SQLAlchemyJobCompanyRepository.recruiter_hiring_pairs(recruiter_id)` already
  returns `[{job_id, hiring_company_id}]` per job — the job ids are discarded
  in `_build_company_detail` (companies_v2_router.py:336-351) after grouping.
- The Jobs page opens a specific job drawer via `/jobs?job=<id>` and the
  Companies page adapter provides `onOpenJob(id)` →
  `window.location.href = /jobs?job=<id>` (widgets/companies-page/index.tsx:39).

## Design Decision (confirmed with user)

Rows **link to the actual jobs**. Each hiring company row expands into links
for the jobs it was published for, each opening the job detail drawer. The
hiring company name stays as a secondary link.

## Implementation Steps

1. **Backend**:
   - Add `RecruiterJobRefSchema` (`id`, `title`, `location`) and add
     `jobs: list[RecruiterJobRefSchema]` to `RecruiterForSchema`.
   - Add `IJobRepository.get_by_ids(job_ids)` + SQLAlchemy impl (batch fetch
     `id`, `title`, `location` for non-deleted jobs).
   - In `_build_company_detail`, group `recruiter_hiring_pairs` output by
     `hiring_company_id` keeping job ids, batch-load titles, and build
     `RecruiterForSchema` entries with `jobs`.
2. **Frontend**:
   - Add `RecruiterJobRef` interface + `jobs` to `RecruiterForCompany`.
   - `CompanyDetailDrawer` "Recruiter for" section: render each job of a hiring
     company as a link (title) calling `onOpenJob(job.id)`; company name link
     stays as a secondary reference.
3. **Tests**:
   - Backend: detail API test asserting `recruiter_for[].jobs` (ids/titles)
     and a repo test for `get_by_ids`.
   - Frontend: drawer test that job links render and invoke `onOpenJob`.
4. **Docs**: `docs/api/companies/company-detail.md` (`recruiter_for[].jobs`),
   `docs/ux/features/companies/company-detail.md` (section behavior),
   `DESIGN.md` wireframe.

## Testing Requirements

- `uv run pytest apps/backend/tests/ -q` green.
- `cd apps/frontend && npx vitest run` green (typecheck/lint pre-existing
  failures untouched).

## Constraints

- Use the same `recruiter_hiring_pairs` semantics so the jobs shown always
  match `recruiter_job_count`.
- Do not add API routes to `entrypoints/api.py`; use per-context routers.
- AGENTS.md rule 13: UX wireframes must be updated.
