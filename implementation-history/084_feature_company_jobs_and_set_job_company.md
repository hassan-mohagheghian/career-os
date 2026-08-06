# Prompt 084 - Company Jobs List + Set Company in Job Detail

## Objective

Two related capabilities:

1. **List the company's connected jobs in the Company Detail drawer.** The
   "Linked Jobs" section (backed by `company.jobs` from the detail payload)
   existed but rendered the raw job UUID as the primary label and dropped the
   canonical score fields. Enhance it to show role, location, Fit/Success/
   Overall scores and an overall grade badge.
2. **Set the company for a job in the Job Detail drawer.** Add a backend
   endpoint to link/unlink a job to a company, and a searchable company picker
   in the Job Detail drawer's Details section.

## Current State

- `GET /api/companies/{id}` already returns `jobs` (`CompanyJobRefSchema` with
  `fit_score`/`success_score`/`overall_score`); the drawer rendered them via
  the legacy `CompanyJobsTab`, which showed `j.id` (UUID) and only legacy
  `j.score`.
- Jobs store `company` (name) and `company_id` columns. `update_job` (PATCH)
  only edits the name; there is no way to set `company_id`.
- `RelateCompanyDialog` shows the searchable-company pattern (DebouncedInput +
  `companyApi.listInfinite`).

## Implementation Steps

### Backend

1. `schemas/jobs_v2.py`: add `SetJobCompanyRequest` (`company_id: str | None`,
   normalized so `""` becomes `None`).
2. `sa_job_repository.py`: add `set_company(job_id, company_id, company_name=None)`
   reusing `update_fields`.
3. `jobs_v2_router.py`: add `PUT /{job_id}/company`. Verifies the job exists
   (404), verifies the company exists when linking (404), writes `company_id`
   (and the canonical name when linking), returns the updated detail payload.
   Extract a shared `_job_detail_payload(job_dict, latest_execution)` helper
   used by the new endpoint.

### Frontend

4. `entities/job/api.ts`: add `jobApi.setCompany(jobId, companyId | null)`.
5. New `features/jobs-v2/components/CompanyPicker.tsx`: searchable popover
   (DebouncedInput + `companyApi.listInfinite`) that calls `onSelect(companyId)`
   and offers **Unlink company** when a company is linked.
6. `JobDetailDrawer.tsx`: add a `Company` row in the Details section wired to a
   `useMutation` that calls `jobApi.setCompany` and invalidates
   `['job-detail', jobId]` + `['jobs']`.
7. `CompanyJobsTab.tsx`: render role (not UUID), location, Fit/Success/Overall
   badges and an overall `GradeBadge`.

### Tests

8. Backend: `TestJobCompanyV2API` — link sets canonical name, null/empty
   unlinks without touching the name, missing job → 404, missing company → 404.
9. Frontend: new `CompanyPicker.test.tsx` (empty state, pick calls onSelect,
   unlink calls onSelect(null)); `JobDetailDrawer.test.tsx` disambiguated the
   now-duplicated company name text and asserts the `Change company` button.

### Docs

10. `docs/ux/features/companies/company-detail.md`: Linked Jobs wireframe with
    scores + grade.
11. `docs/ux/features/jobs/page.md`: "Job Details — Set Company" section.
12. `docs/api/jobs/list-jobs.md`: "Set Job Company" endpoint section.
13. `DESIGN.md`: Job Details drawer Details row (company picker) + Company
    drawer Linked Jobs wireframe.

## Testing Requirements

- Backend: 1226 passed.
- Frontend: 385 passed (48 files); `tsc --noEmit` only baseline errors.

## Constraints

- Feature → SemVer MINOR bump to **3.5.0** in all version locations +
  `check-version.sh`.
