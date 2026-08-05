# Prompt 075 - Companies: UUID v7 IDs + All-in-One Detail API

## Objective

Post-v3.0.0 change request:

1. Give companies **UUID v7** identifiers: `id` fields and every company API
   now takes/returns string UUIDs (mirrors the Jobs UUID migration).
2. Return **all** company info from a **single detail API** (like the Jobs v2
   detail) so the Company drawer fetches once; remove the separate `/links`,
   `/jobs` and Processing History / local-history calls from the drawer.
3. Keep the legacy mutation endpoints (`/companies/{id}/notes|links|jobs|
   intelligence`) and keep `useLocalHistory` + `/api/local-history*` for the
   Skills context — only the company drawer stops using them.

## Current State (Before)

- `CompanyModel.id` is an auto-increment **integer** PK; `company_id` on
  `company_intelligence`, `company_links` and `job.jobs` are int FKs. All
  company API routes use `id: int`.
- Frontend types company ids as `number` everywhere; `CompanyNotesTab` and
  `CompanyJobsTab` each fetch `/api/companies/{id}/links` and
  `/api/companies/{id}/jobs` separately; `CompanyDetailDrawer` calls
  `useLocalHistory({ context: 'company', company_id })` for a collapsible
  Processing History panel.
- The legacy `GET /api/companies/{id}` returns base fields + notes +
  intelligence, but notes/links/jobs are not in one payload.

## Implementation Steps

1. **Backend model layer** — `CompanyModel.id` → `String(36)` PK with
   `default=lambda: str(uuid.uuid7())`; `CompanyIntelligenceModel.company_id`,
   `CompanyLinkModel.company_id`, `JobModel.company_id` → `String(36)` FKs.
2. **Migration** — `apps/alembic/company/versions/company_002_add_uuid_v7.py`
   (`revision: company_002_add_uuid_v7`, `down_revision:
   shared_003_remove_score_weight`): in-place re-key (rewrite
   `company.companies`, `company.company_intelligence`, `company.company_links`,
   `job.jobs.company_id`), backfill UUID v7, drop int PK, recreate constraints
   and indexes. Applied and verified (28 companies, 28 intelligence, 24 links,
   283 jobs, 0 orphans).
3. **Backend int → str threading** — repos, domain interfaces/entities,
   routers (`companies_router`, `root_router`, `jobs_v2_router`,
   `dashboard_router`), TaskIQ client/tasks, workers (`worker_base`,
   `company_worker`, `company_worker_oop`), `execution_runner`, AI graph
   state, schemas (`companies_v2`, `companies`), and processing event models
   all moved from int to string ids (`ProcessHandle.pid` stays int).
4. **All-in-one detail API** — added `GET /api/companies/list/{id}` to
   `companies_v2_router.py` (registered before the legacy router so it shadows
   `/companies/{id}`). Returns base fields + `status`/`current_node`/
   `progress_pct`/`error` + `notes` (parsed `note:` links) + `links` +
   `intelligence` + `scores` + `jobs` (slim projection) + `job_count` in one
   payload (`CompanyDetailResponseSchema`).
5. **Frontend — single payload** — `CompanyDetail`/`CompanyListItem`/`PendingCompany`
   ids → `string`; `entities/company/{types,api,hooks}.ts` string ids;
   `CompanyNotesTab` reads `company.links` from the payload (removed the
   `/links` fetch; notes refresh via `/notes` after mutations);
   `CompanyJobsTab` accepts `jobs` from the payload (removed `/jobs` fetch);
   `CompanyDetailDrawer` dropped `useLocalHistory` + Processing History panel,
   passes `jobs={company.jobs}` to the Jobs tab.
6. **Frontend — id types** — `CompanyRow`, `CompanyActions`, `CompaniesTable`,
   `CompaniesPage`, `CompanyEditDrawer`, `widgets/companies-page/index.tsx`
   (incl. `?company=` deep-link no longer parsed via `Number(...)`), and
   `entities/job/types.ts` (`linked_company`, `company_id` → string).
7. **Docs** — `docs/api/companies/company-detail.md` (new), updated
   `docs/api/companies/list-companies.md`, `docs/ux/features/companies/
   {company-detail,page}.md`, `docs/ux/README.md`, and this history file.

## Testing Requirements

- Backend: uuid company CRUD, detail endpoint single payload (notes/links/
  intelligence/scores/jobs/job_count), 404 for unknown uuid, list pagination
  still green, all workers/processing/repo tests use uuid strings.
- Frontend: `CompanyJobsTab` renders from payload / empty state / `onOpenJob`;
  `CompanyNotesTab` unchanged behavior; drawer consumes single payload; no
  `number` id type errors in the companies feature.
- Full suites: `uv run pytest apps/backend/tests/ -v`,
  `uv run pytest apps/backend/tests/ai -q`,
  `cd apps/frontend && npx vitest run`, `npm run typecheck`, `npm run lint`.

## Constraints

- In-place alembic data migration (no table swap), mirroring the Jobs UUID
  migration; `alembic_version.version_num` is `varchar(32)` — keep revision ids
  short.
- Keep legacy mutation endpoints and `useLocalHistory` for Skills.
- AGENTS.md rules: all AI calls via LLMService, SQLAlchemy ORM, per-context
  routers, default sort newest first, delete on every card, wireframe docs for
  every UI change.
