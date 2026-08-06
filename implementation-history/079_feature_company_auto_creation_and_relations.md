# Prompt 079 - Company Auto-Creation from Jobs + Main/Related Companies

## Objective

1. **During job processing**, extract the company name **and** company URL in the
   single `job.analyze` LLM call, then automatically create or link a Company:
   - If an existing company matches (domain / normalized name / conservative
     fuzzy), just connect the job to it (`job.company_id`) — never create a
     duplicate.
   - If nothing matches, create a minimal company (`status: created`,
     `source: job`) and connect the job to it.
   - The step is **best-effort**: a company extraction/link failure never fails
     the job execution.
2. **Main / related companies**: a company can be related to a **main company**
   (`parent_company_id` self-FK). An alias is a near-duplicate of the main. The
   main is the single reference for display and further processing. Relating
   re-points the alias's jobs (and its own aliases' jobs) to the main.
3. **Company page** stays the home for enrichment and intelligence processing
   (add link/note + reprocess already exist). No auto-queue of
   `COMPANY_PROCESSING` for auto-created companies.

## Current State

- `job.companies` has `company_id` (nullable String(36), no FK) but the
  JOB_PROCESSING LangGraph pipeline never populates it — `job.analyze` extracts
  only the company **name** and `persist_node._persist_job` writes only
  `company` (no `company_url`, no `company_id`).
- Companies are created manually via `POST /api/companies`
  (`CompanyService.create_from_intake`) and processed via the existing
  two-phase `COMPANY_PROCESSING` pipeline. `POST /api/companies/{id}/reprocess`
  queues reprocessing. Notes/links CRUD already exist.
- No company merge / alias / related / canonical concept exists anywhere.

## Implementation Steps

### Backend — Job analysis schema + prompt

1. `processing/application/services/job_analysis_prompt.py`:
   - Add `"company_url": nullable_str` to the output schema after `company`.
   - Prompt: extract the company's website into `company_url` when present.
   - Bump `JOB_ANALYSIS_PROMPT_VERSION` → `1.2.0`.
2. `processing/application/services/job_analysis_validation.py`: add
   `company_url: str | None = None` to `JobAnalysisOutput`.

### Backend — Company matching

3. `companies/domain/repositories/company_repository.py` + `sa_company_repository.py`:
   - `list_for_matching() -> list[dict]` (id, name, website, domain,
     parent_company_id) for all named companies.
   - `count_aliases(company_id) -> int`.
4. `companies/application/services/company_matching_service.py` (new):
   - `normalize_company_name(name)` — lowercase, strip legal-form suffixes
     (GmbH, AG, Ltd, LLC, Inc, Corp, B.V., S.A., Sarl, Srl, plc, oy, ab, nv, as,
     "& co kg"), punctuation → spaces, collapse whitespace.
   - `extract_domain(website)` — scheme/path/port/www stripped.
   - `find_or_create(name, website) -> (company_id, created: bool)`:
     (1) resolve-to-main, (2) exact domain (and root-domain + loose name),
     (3) normalized-name exact, (4) fuzzy `difflib` ratio ≥ 0.88,
     (5) create minimal company. Alias matches resolve to their main.
   - Never queues COMPANY_PROCESSING.

### Backend — Job processing wiring

5. `processing/application/workflows/job_analysis/nodes/link_company_node.py`
   (new): best-effort step reading `fields.company` / `fields.company_url`,
   calls `CompanyMatchingService.find_or_create`, sets
   `job_repo.update_fields(job_id, company_id=...)`, emits SSE step events via
   `progress_ops`. Skips cleanly when no company name.
6. `graph.py`: add `link_company` node between `persist` and `analysis_ready`
   (persist → link_company → analysis_ready; persist-failed → execution_failed).
7. `assembly.py`: build `CompanyMatchingService` (company repo) + job repo and
   inject into `JobAnalysisGraph`.
8. `workflow_step_mapper.py`: add `link_company` → ("link_company", "Link Company")
   to `NODE_TO_STEP` and `WORKFLOW_STEP_IDS`.

### Backend — Main/related companies data model + API

9. New per-context Alembic migration
   `apps/alembic/company/versions/company_005_add_parent_company_id.py`
   (down_revision `company_004_sync_sequences`): add nullable
   `parent_company_id` with self-FK → `company.companies.id`
   (`ondelete="SET NULL"`), indexed.
10. `company_model.py` + domain `company.py` + `mappers.py`: add
    `parent_company_id` (+ self-ref relationship `main_company`, `aliases`).
11. `sa_job_repository.py`: add `reassign_company(from_id, to_id)` (bulk
    `company_id` update on non-deleted jobs).
12. `companies/application/services/company_relation_service.py` (new):
    `relate(company_id, main_id)` and `unrelate(company_id)`; validates
    no self-link, main exists, main is not itself an alias, no cycles; returns
    `{main_company_id, affected_company_ids}` (subtree of the related company).
13. `companies_v2_router.py`: `PUT /api/companies/{id}/main` body
    `{ "main_company_id": str | None }` (null = unrelate); orchestrates
    `CompanyRelationService` + `job_repo.reassign_company` for the affected
    subtree. List + detail responses gain `parent_company_id`,
    `main_company {id, name}`, `alias_count`, `is_alias`.
14. `companies_v2.py` schemas: `CompanyMainRef`, new fields.
15. `jobs_v2_router.py` + `jobs_v2.py`: add `company_id` to
    `JobDetailResponseSchema` (detail + update responses).

### Frontend

16. `entities/company/types.ts` + `api.ts` + `hooks.ts`: new relation fields;
    `setMain(id, mainCompanyId | null)` mutation; query invalidation.
    `entities/job/types.ts`: `JobDetail.company_id`.
17. `JobDetailDrawer.tsx`: company name becomes a clickable chip that opens
    `/companies?company=<company_id>` when `company_id` is present.
18. `CompanyRow.tsx`: alias badge ("Alias of <Main>").
19. `CompanyDetailDrawer.tsx`: alias badge near the name, alias count on main,
    footer "Relate…" action opening a `RelateCompanyDialog` (search + pick main +
    unrelate). Wire through `CompaniesPage`/`CompaniesPageAdapter` + hooks.

### Tests (TDD)

20. Backend:
    - `company_matching_service` unit tests (normalization incl. suffix strip,
      domain match, root-domain match, exact match, fuzzy threshold, alias
      resolution, create-on-miss, empty-website).
    - `link_company_node` tests (link existing, create new, skip, best-effort).
    - relate API tests (set main, unrelate, self-link 409, main-is-alias 409,
      job re-pointing, response fields), company list/detail relation fields,
      job detail `company_id`.
21. Frontend: relate dialog, alias badge, job drawer company chip.

### Docs

22. `docs/ux/features/companies/company-detail.md`, `company-row.md`, `page.md`
    wireframes; new `docs/ux/flows/companies/relate-company.md`;
    `docs/ux/flows/jobs/process-job.md` auto-create step;
    `docs/api/companies/relate-company.md`; `docs/ux/README.md` index;
    `DESIGN.md`; `DOMAIN.md` (Related Companies rule); `API.md` quick-ref row.

### Release

23. MINOR bump → `VERSION`, `CHANGELOG.md` (new top entry), `pyproject.toml`,
    `apps/frontend/package.json`; `./scripts/check-version.sh`; commit + tag.

## Testing Requirements

- Backend: `uv run pytest apps/backend/tests/ -v` (new tests + no regressions).
- Frontend: `cd apps/frontend && npx vitest run` + `npm run lint` + `npm run typecheck`.
- Migration applies cleanly: `alembic upgrade head`.

## Implementation Status — DONE

Implemented in full (2026-08-06):

- **Backend** (`1216` pytest cases pass): `job_analysis_prompt` v1.2.0 + `company_url`
  on `JobAnalysisOutput`; `CompanyMatchingService` (normalize + domain/root-domain/
  exact/fuzzy≥0.88 match, alias→main resolution, minimal `status=created` insert);
  `LinkCompanyNode` wired post-persist in `JobAnalysisGraph` (`link_company` step)
  and injected via `assembly.py`; `company_005_add_parent_company_id` migration
  applied; `CompanyRelationService` (relate/unrelate, subtree job re-pointing);
  `PUT /api/companies/{id}/main` + relation fields on list/detail; job detail
  returns `company_id`. New tests: matching, relation, link node, relate API, job
  detail `company_id`.
- **Frontend** (`369` vitest cases pass): relation fields in company types;
  `setMain` api + mutation; Relate Company dialog (searchable picker + alias
  remove); Related Companies section + alias badge in drawer/row; job detail
  company link → `/companies?company=<id>`.
- **Docs**: `docs/ux/features/companies/relate-company.md`,
  `docs/ux/flows/companies/relate-company.md`, `docs/api/companies/relate-company.md`,
  updated company list/detail/row/page UX + API docs, `docs/ux/README.md` index,
  `DESIGN.md` wireframes.
- **Release**: bumped to `3.3.0` (VERSION, CHANGELOG, pyproject, package.json);
  `./scripts/check-version.sh` passes.

Follow-up (score-source verification, 2026-08-06): confirmed the company list
row scores and the Company Detail drawer scores are exactly what company
processing computed (`build_company_analysis_result` → `persist_analysis` →
`company_intelligence.scores` → normalized `scores` field on list/detail).
Added backend integration tests proving processing→list and processing→detail
score parity, made the drawer read the normalized `company.scores` first
(fallback to `intelligence.scores`), made the row prefer the processing-
computed `overall_grade`, and added vitest coverage for both.

Known pre-existing baseline issues (untouched by this feature): frontend `tsc
--noEmit` fails on ~112 lines (ConfirmDialog, DuplicateJobDialog, ResumeTab, ...)
and `next lint`/`eslint` have no valid config in this checkout.

## Constraints

- All AI calls via `LLMService` (only entry point). No raw SQL outside migrations.
- `link_company` is best-effort — never fails the job execution.
- Contexts must not cross-import: the job graph (processing context) wires the
  companies application service; the relate endpoint (companies presentation)
  composes the jobs repository for job re-pointing.
- Matching is conservative (domain + exact + high-threshold fuzzy) to avoid
  false-positive links; wrong links can be un-related manually later.
- Auto-created companies get `status: created` and are **not** queued for
  intelligence processing.
