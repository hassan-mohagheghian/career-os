# Prompt 164 - Company Type Column, Colors, and Job Context

## Objective
Surface the **company type** across the platform and color-code company rows:

1. Add a **Company Type** column to the company list (`CompaniesTable`/`CompanyRow`).
2. **Color company rows by company type** (per-type tint) in the company list.
3. Show company type in the **related company drawers** (company detail / edit).
4. In the **job application page**, add a **link to the company** (mirroring the
   job drawer's company link to `/companies?company=<id>`).
5. In the **job application page and the job drawer**, show the **company type**
   when it is set.

## Current State
- `CompanyListItem` already carries `company_type`; the list shows Name,
  Industry, Location, Size, Jobs, Scores, Status, Updated, Created (no Type).
- `CompanyRow` tints only recruiter rows purple via `isRecruiterCompany`.
- `CompanyDetailDrawer` already shows a company type badge (local copy of
  `COMPANY_TYPE_LABELS`); `CompanyEditDrawer` has a company type field.
- `JobDetail` (frontend) and `JobDetailResponseSchema` (backend) expose
  `company_id`/`company_name` but **not** `company_type`.
- `JobDetailDrawer` links to the linked company via `CompanyPicker`
  (`/companies?company=<id>`); `WorkspaceHeader` (application page) shows the
  company name as plain text, no link, no type.

## Implementation Steps
1. **Shared company-type helper** (`entities/company/lib.ts`): centralize
   `COMPANY_TYPE_LABELS`, `formatCompanyType(type)`, and
   `COMPANY_TYPE_ROW_CLASSES` + `companyTypeRowClasses(type)` returning per-type
   row tint classes (PRODUCT blue, RECRUITING/STAFFING purple, CONSULTING teal,
   UNKNOWN muted). Reuse in `CompanyDetailDrawer` (drop its local copy).
2. **Company list Type column**: add a `Type` `ColumnDef` to `CompaniesTable`,
   add the column width to `companiesColumns.ts` grid template, and render the
   formatted type in `CompanyRow` (as a compact badge). Color the row by
   `companyTypeRowClasses`, falling back to the recruiter purple tint when no
   type is set but `isRecruiterCompany` is true.
3. **Backend**: add `company_type: str | None = None` to
   `JobDetailResponseSchema`. Populate it in `get_job_detail`,
   `_job_detail_payload`, and `set_job_company` by reading the linked company
   via `company_repo.get_by_id(job_dict["company_id"])`.
4. **Frontend JobDetail type**: add `company_type?: string | null` to `JobDetail`.
5. **Job drawer**: show company type when set (a `Type` detail row / badge next
   to the Company row).
6. **Application page** (`WorkspaceHeader`): make the company name a link to
   `/companies?company=<id>` (when `company_id` is set, mirroring the job
   drawer) and show a company type badge when set.

## Testing Requirements
- Backend: extend the job detail test to assert `company_type` is populated for
  a job linked to a company (and null/absent when unlinked).
- Frontend: add tests for the company row Type column and per-type tint classes;
  add a job-drawer test asserting the company type badge renders when set; add
  an application-workspace/header test asserting the company link and type badge.
- Run backend `uv run pytest tests/jobs -q` and frontend `npx vitest run` +
  `npm run typecheck`; all must pass.

## Constraints
- Frontend TypeScript only; follow AGENTS.md rules (no comments, structlog/UX
  doc updates, DDD). Add wireframe/doc updates to `docs/ux/features/companies/`
  (page + row) and `docs/ux/features/jobs/job-row.md`, and note the application
  header change in `docs/ux/features/applications/workspace.md`.
- Preserve existing `isRecruiterCompany` semantics used elsewhere
  (`data-recruiter`, recruiter job counts).
