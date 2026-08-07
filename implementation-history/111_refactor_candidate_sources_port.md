# Prompt 111 - Port Resume/LinkedIn Into Candidate Sources + Remove Tailored Generation

## Objective

Complete the migration of the legacy resume / LinkedIn experience into the
Candidate module (110 roadmap):

1. **Port storage**: existing `job.resumes` data (`original_*`, `linkedin_*`)
   is migrated into `candidate.candidate_sources` (now with a `raw_text`
   column); the legacy `job.resumes` table is dropped.
2. **Remove the old UI and endpoints**: Resume page (`/resume`), `/api/resumes`
   and `/api/linkedin` routers, resume service + repository, and the Resume /
   LinkedIn entities on the frontend.
3. **Remove tailored resume / cover-letter generation** for jobs (user
   directive): `generate-resume` / `generate-cover`, `generation_worker`,
   tailored/pending-generation repositories, resume AI graphs/tools, TaskIQ
   `process_generation_task`, the generation `ExecutionType`s, and the
   `generation` source in the generation-history UI.
4. **New upload path**: `POST /candidates/sources` accepts
   `{source_type: "resume"|"linkedin", raw_text}`, stores it masked as the next
   version of the current candidate profile, and ProfileImportPage uses it.

All AI calls stay behind `LLMService`; all DB access stays on SQLAlchemy ORM;
cross-context references stay logical (AGENTS.md rule 15). Domain events stay
in-memory (rule 16).

---

# Read Documentation First

Before making changes read:

- docs/ux/features/candidate/profile-import.md
- docs/ux/flows/candidate/import-profile.md
- docs/ux/features/resume/page.md
- docs/api/api-design.md
- docs/database/alembic-guide.md
- apps/backend/candidates/... (router, repositories, models, adapters)
- apps/backend/processing/application/workflows/candidate_source_preparation/
- apps/backend/processing/application/workflows/job_analysis/nodes/prepare_profile_node.py
- apps/backend/processing/infrastructure/workflow/assembly.py
- apps/frontend/src/features/candidate-v2/components/ProfileImportPage.tsx
- apps/frontend/src/entities/candidate/...

---

# Current State

- `candidate_sources` (CandidateSourceModel) has no `raw_text`; repo only has
  create / list_for_profile / get_by_type_and_version / update.
- Resume + LinkedIn adapters (`candidates/application/adapters/`) read
  `job.resumes` via `IResumeRepository` (`original_*`, `linkedin_*` prefixes).
- `PrepareSourcesNode` uses `build_adapter(source_type, resume_repo)`.
- `PrepareProfileNode` falls back to `resume_repo.get_latest_original_raw_text()`
  / `get_latest_linkedin_raw_text()` when no candidate profile exists.
- `assembly.py` wires `SQLAlchemyResumeRepository` into both graphs.
- Legacy routers: `jobs/presentation/api/resumes_router.py`,
  `linkedin_router.py`, `tailored_documents_router.py` (registered in
  `root_router.py`), plus `resumes/active-generations` compat route.
- Legacy `job.resumes` is also read by `stream_server.py` (dead WS pipeline),
  `jobs/infrastructure/workers/worker.py` and `ai/graphs/job/graph.py`.
- Tailored generation: `jobs_router` `generate-resume` / `generate-cover`,
  `generation_worker.py`, `sa_tailored_document_repository.py`,
  `sa_pending_generation_repository.py`, `ai/graphs/resume/*`, `resume_tools.py`,
  TaskIQ `process_generation_task`, `ExecutionType.{RESUME,COVER}_GENERATION`
  + `RESUME_OPTIMIZATION`, `execution_runner.py` branch.
- Generation-history: `generation_models.py` `GenerationSource.{RESUME,COVER_LETTER}`
  + step configs; `generation_repository._query_pending_generations*` (return `[]`);
  frontend `GenerationHistoryDrawer` filter options, `SOURCE_CONFIG.generation`,
  `GenerationProgressCard` resume/cover STEP_CONFIGS.
- Frontend: `/resume` page (ResumeTab, useResume dead hook), entities/resume,
  entities/linkedin, ResumePreview, ProfileImportPage calls legacy uploads.

---

# Implementation Steps

## 1. Candidate source storage (TDD first)

1. Add `raw_text` column to `CandidateSourceModel`.
2. Extend `ICandidateSourceRepository`: `get_latest_by_type(profile_id,
   source_type)`, `get_next_version(profile_id, source_type)`; persist
   `raw_text` in create/update + mappers.
3. Add `POST /candidates/sources` to `candidates_router.py`:
   `{source_type, raw_text}` → get_or_create current profile, next version,
   store `mask_pii(raw_text)` with `status="pending"`, emit
   `CandidateSourceAdded`, return `{source_type, version, status, id}`.
   Reject source types other than resume/linkedin.
4. Alembic (candidate schema): autogenerate `raw_text` column + tune a backfill
   that copies `job.resumes` `original_*`/`linkedin_*` rows into
   `candidate_sources` (create default candidate+profile if none; status
   `processed`, processed_at set). Verify history/heads/upgrade round-trip.
5. `PrepareSourcesNode._known_source_versions` must only skip `processed`
   sources so freshly-uploaded pending rows are picked up.

## 2. Repoint consumers

1. Adapters read `source_repo.get_latest_by_type(profile_id, source_type)`;
   `build_adapter(source_type, source_repo, profile_id)`; drop `resume_repo`.
2. `PrepareSourcesNode`: drop `resume_repo`, use `source_repo` + profile_id.
3. `PrepareProfileNode`: replace `resume_repo` with `source_repo`; fallback
   reads latest resume/linkedin raw text from candidate_sources.
4. `assembly.py`: wire `SQLAlchemyCandidateSourceRepository`, drop
   `SQLAlchemyResumeRepository`.
5. Update tests (adapters, candidate extract service integration, job analysis,
   candidate processing).

## 3. Remove tailored generation + legacy resume/LinkedIn

1. Delete `resumes_router.py`, `linkedin_router.py`,
   `tailored_documents_router.py` + root_router registrations + compat route.
2. Delete resume service/repository/entities/schemas, tailored + pending
   generation repositories, `generation_worker.py`, resume AI graphs/tools,
   job `generate-resume`/`generate-cover` endpoints.
3. Remove `ExecutionType.{RESUME,COVER}_GENERATION` + `RESUME_OPTIMIZATION`,
   `execution_runner` branch, TaskIQ `process_generation_task` +
   `enqueue_generation`, `background.generate_resume_task`.
4. Dead paths: delete `stream_server.py` + tests; remove resume reads from
   `worker.py` + `ai/graphs/job/graph.py`.
5. `generation_models.py`: drop resume/cover source members + step configs +
   history mapping; `generation_repository.py`: drop generation queries.
6. Cleanup dependencies, jobs infrastructure exports, `db.py` file migration,
   `sa_job_repository.delete_by_id` resume deletion, `ResumeModel` removal.
7. Alembic (job schema): drop `job.resumes` after the candidate backfill.
8. Update affected tests + conftests.

## 4. Frontend

1. `entities/candidate`: add `uploadSource(sourceType, rawText)`.
2. `ProfileImportPage`: use candidate upload; drop resume/linkedin entities.
3. Delete `/resume` page, resume-page widget, features/resume, entities/resume,
   entities/linkedin, ResumePreview (+ tests).
4. Remove `resume` nav item + Header test update.
5. Generation-history cleanup: drawer filters, `sourceConfig`, `sourceConfig`
   test, `GenerationProgressCard` resume/cover configs.

## 5. Docs

Update `docs/ux/README.md`, `DESIGN.md`, profile-import + import-profile docs
(POST /candidates/sources), `docs/api/api-design.md`, candidate events doc,
API/ARCHITECTURE/DOMAIN/workflows as needed.

---

# Testing Requirements

Backend (`uv run pytest apps/backend/tests/ -v`):

- Source repo: latest-by-type + next-version.
- `POST /candidates/sources`: creates pending masked row, increments version,
  masks PII, rejects unknown source type.
- Extract service: pending → processed transition.
- Adapters + job analysis fallback read candidate_sources.
- Removed routers/endpoints gone; conftests updated.

Frontend (`cd apps/frontend && npx vitest run`, plus `npm run lint` and
`npm run typecheck`):

- ProfileImportPage uploads via candidate API.
- Nav/header + generation-history tests updated.

Alembic: `uv run alembic history`, `uv run alembic heads` (single),
`uv run alembic upgrade head`, downgrade/upgrade round-trip (rule 14).

---

# Important Constraints

- Migrate before dropping: candidate backfill migration must run before the
  job `job.resumes` drop.
- Keep `mask_pii` PII masking on upload (existing privacy behavior).
- Do not reintroduce cross-context DB foreign keys (rule 15).
- Events stay in-memory only; do not build pub/sub (rule 16).
- No UI change ships without wireframe docs (rule 13).
- Version bump (MINOR) across VERSION / CHANGELOG / pyproject / package.json;
  `./scripts/check-version.sh` must pass.

---

# Completion Log

Frontend portion (steps 3–5) completed in a follow-up pass:

- Deleted `/resume` route, `widgets/resume-page`, `features/resume`,
  `entities/resume`, `entities/linkedin`, `shared/components/ResumePreview` +
  test, and the `.resume-preview-container` CSS block.
- Removed the `resume` nav item (+ `FileText` import) from `nav-items.ts`;
  updated `Header.test.tsx`.
- Added `candidateApi.uploadSource(sourceType, rawText)` →
  `POST /candidates/sources` (with `api.test.ts`) and rewired
  `ProfileImportPage` Save Resume / Save Profile to use it.
- Trimmed the `generation` source from `GenerationHistoryDrawer` filter options,
  `sourceConfig.ts` (+ test) and `GenerationProgressCard` resume/cover step
  configs.
- Docs: deleted `docs/ux/features/resume/page.md`; updated `docs/ux/README.md`
  index, `docs/ux/app-shell.md` nav, `DESIGN.md` nav tree, and
  `docs/ux/features/candidate/profile-import.md` +
  `docs/ux/flows/candidate/import-profile.md` (now `POST /api/candidates/sources`);
  synced `docs/database/sqlalchemy-architecture.md` + `docs/architecture/`
  (removed `resumes` table / resume graphs / resume_tools.py).
- Verified: frontend `npx vitest run` (446 passed) + `npm run typecheck` (49
  pre-existing errors, none new); backend `uv run pytest apps/backend/tests/`
  (1391 passed).
