# Changelog

## [3.1.0] — 2026-08-05

### Added

- **All-in-one Company detail API** — `GET /api/companies/list/{id}` returns
  every company field plus processing status, notes, links, intelligence,
  scores, linked jobs and `job_count` in a single payload (mirrors the Jobs v2
  detail). The Company detail drawer now fetches once; the Original Notes and
  Jobs tabs read from that payload instead of making separate `/links` and
  `/jobs` calls, and the Processing History panel was removed from the drawer.

### Changed

- **Companies now use UUID v7 identifiers** — `company.companies.id` is a
  `varchar(36)` UUID v7 primary key, and `company_id` on `company_intelligence`,
  `company_links` and `job.jobs` are strings (in-place Alembic data migration
  `company_002_add_uuid_v7`). Every company API route, repository, worker and
  processing event now takes/returns string ids; the frontend company and job
  entity types follow suit (`?company=` deep-links no longer coerce to numbers).

## [3.0.0] — 2026-08-05

### Added

- **Companies V2 workspace** — the Companies page is rebuilt to parity with the
  modern Jobs V2 UX: a virtualized, cursor-paginated, infinitely loading company
  table backed by the new `GET /api/companies/list` endpoint (search, industry
  filter, name/date/score sorting with NULLS LAST). Sheet-based drawers replace
  the legacy component stack:
  - **Company Detail drawer** — overall grade + Fit/Success/Overall score
    cards, processing history (`/api/local-history?context=company`), and tabs
    for Original Notes, Intelligence (product vs. recruiter variants), Scores,
    and linked Jobs.
  - **Add Company drawer** — free-text notes and links are posted to
    `POST /api/pending-companies` (source `web`) to seed the legacy processing
    pipeline; success opens the Company Queue drawer.
  - **Edit Company drawer** — edits core fields via `PUT /api/companies/{id}`
    and invalidates the list and detail queries.
  - **Company Queue drawer** — monitors the legacy `pending_companies`
    pipeline (created/pending/queued/processing/failed+cancelled sections)
    by polling `GET /api/pending-companies` every 5s with Process/Delete
    actions.
  - The row grade badge reuses the shared A++…D tokens; scores render as
    compact F/S/O badges with the shared score colors; fractional score values
    (e.g. `38.5`) are now accepted by `CompanyScoresSchema`
    (`overall`/`fit`/`success` are `float`, not `int`).

### Changed

- The Companies page supports `?company={id}` deep-linking; opening a drawer
  sets the parameter and closing it clears it.
- Dead legacy companies UI was removed: `CompaniesPage`, `CompanyDrawer`,
  `CompanyCard`, `CompanyProcessingItem`, `ScoreBar`, the seven
  `Company{Status}Card` components, and `useCompanies` (the hook directory and
  its shared export). `CompanyJobsTab`/`CompanyNotesTab` were kept and are now
  imported by the new detail drawer.
- `docs/ux/features/companies/{page,company-row,company-detail,add-company,edit-company,company-queue}.md`,
  `docs/ux/flows/companies/browse-companies.md`, and
  `docs/api/companies/list-companies.md` document the new workspace; the
  `docs/ux/README.md` index and `DESIGN.md` wireframes were updated.
- `implementation-history/074_feature_companies_v2_parity.md` records the full
  plan and outcome.

## [2.9.0] — 2026-08-05

### Added

- **Job favorites** — each job carries a user-managed `favorite` flag. Rows in
  the V2 jobs list gain a dedicated star column (first column, pinned) that
  toggles the flag optimistically via the new `PUT /api/jobs/{job_id}/favorite`
  endpoint. The toolbar gains a star toggle filter (`GET /api/jobs/list?favorite=true`)
  that shows only favorited jobs. The flag is managed exclusively by its own
  endpoint and is not part of the Edit Job payload.
  - Migration `job_003_add_job_favorite` adds `favorite` (Integer, NOT NULL,
    `server_default '0'`) to `job.jobs`; `JobModel`, the `Job` entity and
    `job_model_to_dict` carry it; `SQLAlchemyJobRepository.search_jobs_cursor`
    gained a `favorite` filter and a new `set_favorite` method.

- **Recommendation tags** — the analysis recommendation (`apply` / `consider` /
  `skip`) is now shown as a colored badge in a dedicated Recommendation column
  (after Scores) on each V2 list row. It is batch-loaded per page
  (`recommendations_by_job_ids`, no N+1) and is `null` for jobs without a
  completed analysis. The list item now exposes the lightweight
  `recommendation` field while the full `analysis` block stays on the detail
  endpoint.

- **Recommendation filter** — the toolbar gains a Recommendation select
  (All / Apply / Consider / Skip) backed by
  `GET /api/jobs/list?recommendation=apply|consider|skip`. Jobs without an
  analysis row never match; invalid values return 422. It composes with the
  other filters (e.g. `favorite=true`).

### Changed

- `docs/api/jobs/list-jobs.md`, `docs/domain/jobs/job-list-item.md`,
  `docs/ux/features/jobs/page.md`, `docs/ux/features/jobs/job-row.md`,
  `docs/ux/features/jobs/favorite-job.md` (new), `API.md`, and `DOMAIN.md`
  document the favorite flag, the recommendation field/column, and both
  filters.
- `implementation-history/068_feature_job_favorites_and_recommendation_tags.md`
  records the full plan (favorites + recommendation tags + recommendation
  filter).

### Tests

- Backend: `tests/jobs/presentation/api/test_jobs_v2_api.py` gained
  `TestJobFavoritesV2API` (default false, favorite filter, toggle persists,
  404), `TestJobRecommendationV2API` (field present, populated from analysis,
  null without analysis) and `TestJobRecommendationFilterV2API` (per-value
  filter, excludes jobs without analysis, combines with favorite, 422).
- Frontend: `JobsToolbar.test.tsx` (favorite + recommendation filter
  controls), `useJobsInfiniteQuery.test.tsx` (favorite filter/mutation,
  recommendation filter flows into the query and clear), plus new
  `FavoriteButton.test.tsx`, `RecommendationBadge.test.tsx` and `JobRow.test.tsx`.

## [2.8.0] — 2026-08-04

### Changed

- **Job list is now driven by `processing_executions`, not legacy status** —
  `GET /api/jobs/list` no longer reads `jobs.status`. Each row carries a
  projection of the job's **latest** execution (id, status, started/finished
  timestamps); `job_status` is that execution's status (`null` when the job has
  never been processed). The `processing_status` filter matches only jobs whose
  latest execution (by `created_at`) has the given status, and the legacy
  `JobListItem` payload keeps working through the cursor-based
  `search_jobs_cursor` which now filters by `job_ids` instead of
  `processing_status`.
  - `SQLAlchemyProcessingExecutionRepository` gained `latest_by_target_ids`
    (batch latest lookup, no N+1) and `target_ids_with_status` (single window
    query over `created_at desc` per target).
  - The persist node now bumps `updated_at` whenever it writes analysis fields
    or scores, so a completed execution surfaces at the top of the default
    (updated_at desc) sort.

- **Completed/failed/cancelled executions refresh the job list** —
  `useProcessingEvents` now invalidates the `jobs-v2-infinite` queries when an
  execution reaches a terminal state, so the row is refetched and shows the
  persisted pipeline output (extracted title/company, scores, final status)
  across reloads. Non-terminal events still update the row in place only.

### Added

- **Backend tests** — `tests/processing/infrastructure/repositories/test_sa_processing_execution_repository.py`
  (latest-per-target batch + latest-only status filter), updated
  `tests/jobs/presentation/api/test_jobs_v2_api.py` (real execution projection,
  latest-only filtering, null status without execution, completed-job listing),
  and `tests/jobs/infrastructure/repositories/test_sa_job_repository_extra.py`
  (job_ids filter semantics incl. empty list → no rows).
- **Frontend test** — `src/shared/hooks/useProcessingEvents.test.tsx` asserts
  terminal execution events invalidate the jobs list query while non-terminal
  events do not.

### Docs

- `docs/api/jobs/list-jobs.md`, `docs/domain/jobs/job-list-item.md`,
  `docs/domain/processing/processing-execution.md`,
  `docs/ux/features/jobs/page.md`, `docs/ux/features/jobs/job-row.md`, and
  `docs/ux/flows/jobs/process-job-live.md` updated to document that the list is
  execution-driven (latest execution projection, latest-only status filter, no
  legacy `jobs.status` fallback) and that terminal events trigger a list
  refetch.


## [2.7.0] — 2026-08-04

### Fixed

- **Deleted jobs now disappear from the job list** — the shared HTTP client
  (`apps/frontend/src/shared/api/http-client.ts`) resolved every successful
  response body with `res.json()`, which threw a `SyntaxError` on the empty
  body of `DELETE /api/jobs/{job_id}` (`204 No Content`). The delete call
  always failed client-side, so the Job stayed visible until a manual reload
  even though the server had deleted it. The client now resolves `204`
  responses to `undefined` without parsing.

### Changed

- **Delete Job is now an optimistic update** — `useJobsInfiniteQuery` exposes
  a `deleteMutation` that removes the Job from every loaded page and decrements
  `total_items` immediately after confirmation, snapshots the previous cache
  for rollback on error, and invalidates the `jobs-v2-infinite` queries on
  settle so pagination/cursors stay consistent. The page widget
  (`widgets/jobs-page-v2`) now drives the destructive confirm dialog through
  this mutation instead of calling `jobApi.deleteJob` + `refetch`.

### Added

- **Frontend tests** — `shared/api/http-client.test.ts` (204 handling,
  JSON parsing, error mapping) and `features/jobs-v2/hooks/useJobsInfiniteQuery.test.tsx`
  (optimistic removal + rollback for the delete mutation).

### Docs

- `docs/api/jobs/delete-job.md`, `docs/ux/features/jobs/delete-job.md`,
  `docs/ux/flows/jobs/delete-job.md` updated to document the `204` empty-body
  contract and the optimistic delete flow.
- `docs/agents/delete-job-visuals.md` added — a note for an agent to create
  diagrams, charts, and wireframes for the delete flow in `docs/` as needed.


### Changed

- **Jobs re-keyed to UUID `id` — legacy numeric `num` column removed** (full removal + Alembic migration `job_002_remove_job_num`):
  - `JobModel` no longer has a `num` column; the `id` (UUID v7) column is now the sole primary key.
  - Related tables re-keyed to the job UUID: `summaries` (`job_id`, autoincrement `id` PK replaces `num`), `resumes` (`job_id` replaces `job_num`).
  - Repos renamed accordingly: `get_by_num`→`get_by_id`, `get_num_by_url`→`get_id_by_url`, `get_company_id_by_num`→`get_company_id_by_id`, summary `get_by_num`→`get_by_job_id`; `get_next_num`/`delete(num)` removed in favor of `delete_by_id`.
  - Worker/stream-server helpers flow the job UUID (`job_id`) instead of a numeric `num`.
  - API v2 job list/detail responses no longer include `num`; frontend migrated to `id` everywhere (job types, resume generation endpoints, company-linked job lists, sort fields).

## [2.5.0] — 2026-08-02

### Added

- **Delete Job feature** — permanent hard deletion of a Job and all its related data via **`DELETE /api/jobs/{job_id}`**:
  - Backend: `delete_by_id()` on the Job repository (removes the Job row, supporting summary/resume rows), `delete_by_target()` on the processing-execution repository (purges executions for the target), and a `DELETE` endpoint returning `204`.
  - Frontend: `jobApi.deleteJob`, an icon-only **Delete** row action (trash icon) threaded through `JobRow`/`JobsTable`/`JobsPage`, and a destructive confirmation dialog before deleting.
- **Backend tests** — `test_jobs_v2_delete_api.py` (delete + executions purged, 404 for unknown id, other jobs preserved).
- **Frontend tests** — Delete action renders and fires `onDelete` in `JobActions.test.tsx`.
- **Docs** — `docs/ux/features/jobs/delete-job.md`, `docs/ux/flows/jobs/delete-job.md`, `docs/api/jobs/delete-job.md`; `job-row.md` Actions updated; `docs/ux/README.md` updated.

## [2.4.0] — 2026-08-02

### Added

- **Edit Job feature** — Edit Job Drawer with a **PATCH `/api/jobs/{job_id}`** endpoint and icon-only row action:
  - Backend: `UpdateJobRequest` schema (partial update, whitelisted `EDITABLE_FIELDS`), `update_by_id()` repository method, `JobNoteItem`/`JobLinkItem` models.
  - Notes and Additional Links are now **editable and addable** from the Edit Job drawer (add/remove, persisted on Save), not just read-only.
  - `JobData` notes/links tolerance — jobs with `notes=None`/`links=None` normalize to `"[]"` instead of raising a pydantic `ValidationError`.
  - Workflow errors now use a clear **`[step] error`** prefix (e.g. `[load_job]`, `[validate_context]`) so the failing step is obvious.
- **Frontend tests** — `JobActions.test.tsx` and `JobEditDrawer.test.tsx` (icon-only actions, edit drawer prefill/submit/validation/notes-links).

### Changed

- **All job row actions are now icon-only** with tooltips (Edit, Details, Process, Cancel, Retry, View Progress/Results) — no text labels in the Actions column.
- **Edit Job Drawer layout fixed** — header/scroll/footer now fill the viewport (scroll area uses `flex-1 min-h-0`), so the **Save/Cancel buttons stay visible** instead of being pushed off-screen.
- **Edit-Job docs updated** — notes and links documented as editable in `docs/ux/features/jobs/edit-job.md` and `docs/ux/flows/jobs/edit-job.md`.

### Fixed

- Jobs without notes/links no longer fail workflow load with `JobData notes_raw Input should be a valid string`.
- `links` was missing from `job_model_to_dict` mapper output; now included so the edit/detail responses return them.

## [2.3.0] — 2026-07-27

### Added

- **Generation Domain Models** — `GenerationSource`, `GenerationStatus`, `GenerationRun`, `GenerationHistoryItem` (DDD)
- **Unified Generation History Repository** — reads from ALL 4 source tables (pending_jobs, pending_companies, pending_generations, skill_roadmap_jobs)
- **JobWorker(WorkerBase)** — Template Method pattern for job processing pipeline
- **CompanyWorker(WorkerBase)** — Template Method pattern for company processing pipeline
- **GenerationWorker(WorkerBase)** — Template Method pattern for resume/cover letter generation
- **InsightsService** — OOP wrapper for career intelligence with source type mapping
- **SkillRoadmapService** — OOP wrapper for skill roadmap operations
- **STEP_CONFIGS** — Frontend step configuration map for all 13 generation source types
- **35 new TDD tests** — domain models (16), repository (10), workers (9)

### Changed

- **Generation History API** — `/api/generation-history` now reads from ALL 5 source tables via `GenerationHistoryRepository`
- **GenerationProgressCard** — supports all 13 source types with correct step configurations
- **GenerationHistoryDrawer** — shows all 5 source types with proper icons and colors
- **WorkerBase.\_reset_steps()** — fixed string-to-enum conversion bug
- **WorkerBase.process()** — now persists `step_done` to DB via `_mark_step()`

### Fixed

- **Generation history incomplete** — was only showing pending_generations + skill_roadmap_jobs, now shows all 5 sources
- **Status display** — `done` status (from pending_jobs/companies) now properly displayed as green
- **Duration calculation** — uses `duration_seconds` from API when available

## [2.2.0] — 2026-07-25

### Added

- **AI Agent Orchestration Layer** — Provider abstraction, LLMService, agent runtime, tools, workflow graphs
- **LLMService** — Unified entry point for all AI calls with generate/generate_structured/generate_streaming
- **Provider System** — MimoProvider (production), OpenAIProvider (stub), LocalLLMProvider (stub)
- **Agent Runtime** — AgentState, AgentExecutor, AgentRegistry, GraphBuilder (LangGraph)
- **Tool System** — 10 domain tools wrapping existing services
- **Workflow Graphs** — JobProcessingGraph, CompanyProcessingGraph, InsightsGenerationGraph
- **AI Tests** — 70 tests covering providers, agents, tools, workflows, service
- **Async Resume/Cover Generation** — Background processing with WebSocket progress bars
- **Company Context Enrichment** — Resume/cover prompts enriched with linked company intelligence
- **Generation Progress Tracking** — Step-by-step progress with cancel/retry support
- **Generation History** — Resume/cover generations appear in unified history with session_id

### Changed

- **Python 3.14** — Upgraded from 3.15 for stable langgraph compatibility
- **All AI calls via LLMService** — 15 direct MimoRunner/subprocess calls migrated
- **WebSocket for generation progress** — Replaced polling with real-time updates
- **GitHub Actions** — Updated to Python 3.14

### Fixed

- **sqlite3.Row .get() error** — Generation worker properly converts rows to dicts
- **Double pid prefix** — Removed gen_type prefix from pid since prompts add it
- **Curly braces in prompts** — Escaped JSON content in company context for template.format()

## [2.1.0] — 2026-07-25

### Added

- **TypeScript Conversion** — All 68 frontend files converted from JS/JSX to TS/TSX
- **Feature-Based Frontend Architecture** — `features/{jobs,companies,insights,skills,resume,rules}`, `shared/`, `layout/`
- **Skills as Top-Level Tab** — Independent from Insights, own `useSkills` hook and `SkillsTab` component
- **Generation History Drawer** — Unified history across career-intel, roadmaps, job processing, company processing
- **Version Tracking** — `version` column on `pending_jobs`, `pending_companies` for retry counting
- **Font Size System** — Custom Tailwind tokens `text-3xs` (6px) and `text-2xs` (8px) for consistent dense UI
- **API Documentation** — Swagger UI at `/api/docs/`, ReDoc at `/api/redoc/`, OpenAPI 3.0 spec
- **Stale Run Recovery** — On startup, stuck `processing` jobs marked `failed` with version bump
- **Notes+Links Input** — Both jobs and companies accept multi-source input
- **Skills DB Fill** — AI insights automatically fill extracted skills into tech_stack
- **Comprehensive Documentation** — CONTEXT, DOMAIN, FEATURES, API, DEVELOPMENT, AI_AGENTS, DECISIONS, RUNBOOKS

### Changed

- **Renamed "Career Intel" → "Insights"** — All code, DB references, UI, routes, SocketIO events
- **Feature-based frontend architecture** — `components/` → `features/`, `shared/`, `layout/`
- **Per-section prompts** — `generate_all()` runs each section's dedicated prompt instead of monolithic
- **Session resumption** — Worker passes previous session_id to mimo via `--session` for retry continuity
- **Company scores synced** — Card and drawer now show same Fit/Success/Overall scores
- **Navigation reorganized** — Jobs, Companies, Skills (top-level), Insights (sub-tabs), Settings (Resume, Rules)

### Removed

- **Stale agent docs** — `docs/agent/` directory (session-specific, outdated)
- **career-intel naming** — Replaced with `insights` throughout

## [Previous]

### Added

- **Skill Taxonomy** — 5 categories: Technical, Engineering, Professional, Domain, Career
- **Skill Aliases** — Merge duplicate skills with alias tracking
- **Skill Relationships** — Related, similar, parent, child, alternative links
- **Skill Detail Drawer** — Full skill overview with roadmap, rename, hide, remove
- **Skill Management Endpoints** — hide, restore, rename, delete, merge
- **WebSocket Real-Time Updates** — pending, company, career intelligence, skill roadmap events
- **Career Intelligence System** — 6 sections with per-section generation
- **Company Intelligence** — AI analysis with Fit/Success/Overall scoring
- **Processing Queue** — Persistent queue with concurrent workers
- **Scoring Rules** — Configurable rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING)
