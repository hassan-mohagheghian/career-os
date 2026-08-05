# Prompt 074 - Companies V2: Jobs-V2 UX Parity

## Objective

Bring the Companies workspace to parity with the modern Jobs (v2) UX: a
virtualized, server-paginated company table with a header/toolbar, Sheet-based
Add / Edit / Detail drawers, and a Company Queue drawer that surfaces the
existing legacy company-processing pipeline — without rebuilding that pipeline.
Remove all dead legacy company UI and hook duplication.

## Current State

- `GET /api/companies` returns a plain array (name-sorted, non-empty names)
  with scores merged ad-hoc — no pagination, search, or sort. Jobs v2 has a
  cursor-paginated `/jobs/list` endpoint with typed schemas.
- Company processing runs on a **separate legacy pipeline** (`pending_companies`
  table + `enqueue_company_sync` taskiq + LangGraph company graph + WebSocket
  broadcaster). It does not use the jobs Processing-Execution / SSE model, so
  the jobs `ProcessingDrawer` and `useProcessingEvents` are not reusable; the
  Company Queue must poll `GET /api/pending-companies`.
- The `companies` table itself carries processing columns (`status`,
  `current_node`, `progress_pct`, `error`), enabling an inline processing
  status on company rows.
- Frontend legacy: `CompaniesPage.tsx` (fused left "Processing Companies"
  column + right card grid); the widget never passes `pending`, so the left
  column renders empty in production. `CompanyDrawer.tsx` (AppDrawer) holds the
  rich intelligence tabs worth preserving. Dead components: `CompanyProcessingItem`,
  the status cards (`CompanyCreatedCard` … `CompanyProcessedCard`),
  `useCompanies.ts` (plain fetch) duplicates the unused react-query
  `entities/company/*`. The widget dispatches a dead `openJob` CustomEvent and
  "View All Jobs" / job deep-links are no-ops.

## Implementation Steps

1. Backend — add `GET /api/companies/list` (registered before the legacy route):
   query (`name`, `industry`, `city`, `country`, `description` substring),
   `industry` filter, `sort` (`name`, `created_at`, `updated_at`, `overall_score`,
   `fit_score`, `success_score`), `order`, `page_size`, `cursor`. Response
   `{ items, next_cursor, has_more, total_items }` with typed
   `CompanyListItemSchema` (id, name, industry, city, country, company_size,
   company_type, logo_url, website, description, job_count, scores, processing,
   updated_at, created_at). Repository: `list_paginated(...)` joining job_count
   and intelligence scores, NULLS-LAST on score sorts, default `created_at desc`.
2. Frontend entity layer — expand `entities/company/{types,api,hooks}.ts`:
   `CompanyListItem`, `CompanyScores`, `CompanyProcessing`, `CompanyDetail`,
   `CompanySearchQuery`, `InfiniteCompanySearchResult`; `companyApi.listInfinite/
   get/update/delete/reprocess/pendingList`; react-query `useCompaniesInfiniteQuery`
   (mirroring `useJobsInfiniteQuery`) plus delete/update/reprocess mutations and
   `useCompanyQuery`.
3. Frontend UI — new `features/companies-v2/components/`: `CompaniesPage` shell
   (header + toolbar + table + drawers + ConfirmDialog), `CompaniesHeader`,
   `CompaniesToolbar`, `CompaniesTable` (virtualized + infinite-scroll sentinel),
   `CompanyRow`, `companiesColumns` (reuse `SortableHeader`), `CompanyDetailDrawer`
   (migrate `CompanyDrawer` to `Sheet`, keep intelligence tabs via
   `CompanyNotesTab`/`CompanyJobsTab`), `CompanyEditDrawer` (new, PATCH
   `/api/companies/{id}`), `AddCompanyDrawer` + `AddCompanyForm` (notes/links →
   `POST /api/pending-companies`), `CompanyQueueDrawer` (polls
   `GET /api/pending-companies`; sections created/queued/processing/failed with
   process/retry/pause/move-to-created/delete; delete on every card).
4. Widget — rewire `widgets/companies-page/index.tsx` to react-query, remove the
   `openJob`/`openCompany` CustomEvents, fix `?company=` deep-link, make "View All
   Jobs" navigate to `/jobs`.
5. Cleanup — delete dead components (`CompanyProcessingItem`, status cards,
   legacy `CompaniesPage.tsx`, `ScoreBar` if unused, `useCompanies.ts`) and their
   tests (`CompanyStatusCards.test.tsx`, `CompanyProcessingItem.test.tsx`,
   `CompanyCard.test.tsx`, `ScoreBar.test.tsx`, legacy `CompaniesPage.test.tsx`).
6. Docs — `implementation-history/074_feature_companies_v2_parity.md` (this file);
   `docs/ux/features/companies/{page,company-row,add-company,edit-company,
   company-detail,company-queue}.md` with ASCII wireframes; `docs/ux/flows/companies/
   {browse-companies,add-company,edit-company,delete-company,process-company}.md`;
   update `docs/ux/README.md`, `DESIGN.md`, and `docs/api/companies/list-companies.md`.

## Testing Requirements

- Backend: list endpoint pagination (cursor, has_more), search, industry filter,
  sort + NULLS-LAST, default `created_at desc`.
- Frontend: `CompaniesPage` render/empty/filter/error; `CompanyRow` columns +
  actions; `AddCompanyForm` validation/submit; `CompanyEditDrawer` load/prefill/
  save; `CompanyQueueDrawer` sections + actions; `useCompaniesInfiniteQuery`
  pagination.
- Full suites: `uv run pytest apps/backend/tests/ -v` and
  `cd apps/frontend && npx vitest run`, plus `npm run lint` and `npm run typecheck`.

## Constraints

- Do not rebuild the company processing pipeline (no SSE for companies; the queue
  drawer polls). AGENTS.md rules: all AI calls via LLMService, SQLAlchemy ORM,
  per-context routers (no routes in `entrypoints/api.py`), default sort newest
  first, delete on every card, and rule 13 (wireframe docs for every UI change).
