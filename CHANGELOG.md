# Changelog

## [2.6.0] — 2026-08-02

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
