# Prompt 155 - Company type filter for company list

## Objective

Add a company-type filter to the Companies list toolbar (Product / Recruiting
agency / Staffing / Consulting / Unknown) so users can isolate a given kind of
company, e.g. recruiters.

## Current State

- `GET /api/companies/list` filters by `query`, `industry`, `pinned`, `status`
  via `_matches` (`companies_v2_router.py:115`) — no `company_type` support.
- The frontend toolbar (`CompaniesToolbar.tsx`) has Industry / Status selects
  and a Pinned toggle; state flows from `useCompaniesInfiniteQuery`
  (`entities/company/hooks.ts`) through `CompaniesPage` and the page widget.
- `company_type` values stored: `PRODUCT_COMPANY`, `RECRUITING_AGENCY`,
  `STAFFING_COMPANY`, `CONSULTING_COMPANY`, `UNKNOWN` (plus a few legacy free-text
  values). Labels already exist in `CompanyDetailDrawer` (`COMPANY_TYPE_LABELS`).

## Changes

- `apps/backend/companies/presentation/api/companies_v2_router.py`: add
  `company_type` query param to `list_companies_v2` and filter on it in
  `_matches` (exact match on `row["company_type"]`).
- `apps/frontend/src/entities/company/types.ts`: add `company_type?: string` to
  `CompanySearchQuery`.
- `apps/frontend/src/entities/company/api.ts`: pass `company_type` in
  `listInfinite`.
- `apps/frontend/src/entities/company/hooks.ts`: add `filterCompanyType` state,
  include it in `filterKey`, pass to `listInfinite`, count in
  `activeFilterCount`, reset in `clearFilters`, expose setter.
- `apps/frontend/src/features/companies-v2/components/CompaniesToolbar.tsx`: add
  a Type `Select` (All + the five standard values) using `COMPANY_TYPE_LABELS`.
- `apps/frontend/src/features/companies-v2/components/CompaniesPage.tsx` and
  `apps/frontend/src/widgets/companies-page/index.tsx`: thread the new props.

## Testing Requirements

- Backend: add `test_list_filters_by_company_type` in
  `apps/backend/tests/companies/presentation/api/test_companies_v2_api.py`.
- Frontend: add `CompaniesToolbar company type filter` describe block in
  `CompaniesToolbar.test.tsx` (render, select, active label).
- Run:
  `uv run pytest apps/backend/tests/companies/presentation/api/test_companies_v2_api.py -q`
  and `cd apps/frontend && npx vitest run src/features/companies-v2/components/CompaniesToolbar.test.tsx`.

## Constraints

- No schema/migration change; pure query/filter change. Respect AGENTS.md 13
  (UX doc + wireframe), 2 (implementation history first), 10 (per-context router).
