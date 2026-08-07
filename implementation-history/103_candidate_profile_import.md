# Prompt 103 - Candidate Profile Import (API + Frontend + UX)

## Objective

Implement Phase 103 of the Candidate Profile Domain (master spec
`098_feature_candidate_profile_domain.md`): the `/api/candidates` API router and
the first Candidate frontend page — **Profile Import** (110 Phase 1, "highest
priority"). The page lets the user upload a resume / paste LinkedIn / optionally
enter a GitHub username, run AI profile analysis (candidate processing), then
review the extracted profile (skills, experience, projects, sources, summary)
and confirm. Review is **post-hoc**: extraction already merges + persists via
the Phase 101 workflow; the Review step displays the result and Confirm marks it
acknowledged.

## Decisions (approved in planning Q&A)

1. **Scope**: Profile Import only (110 Phase 1 + 098 Phase 103). Dashboard
   (110 Phase 2) is a later phase.
2. **Post-hoc confirm**: no draft/pending-review state; extraction persists
   through the existing `candidate_processing` workflow; Review displays the
   result with Confirm/Cancel.
3. **History number**: `103` (matches the 098 roadmap label for this phase).

## Current State

- Backend `candidates` bounded context fully built (phases 099-102): entities,
  repos (`ICandidateProfileRepository.get_current_profile` / `list_versions`,
  `ICandidateSourceRepository.list_for_profile`), SQLAlchemy + migration
  `candidate_001`, DI factories in `dependencies.py:86-111`
  (`get_candidate_repo`, `get_candidate_profile_repo`,
  `get_candidate_source_repo`, `get_candidate_extract_service`), lazy infra
  exports in `candidates/infrastructure/__init__.py`. **No presentation layer.**
- `ExecutionType.CANDIDATE_PROCESSING` + two-phase LangGraph wired (Phase 101),
  dispatched via `CreateProcessingExecutionUseCase` +
  `DispatchProcessingExecutionService` (exact pattern:
  `processing/presentation/api/process_router.py:20-42`,
  `shared/presentation/api/root_router.py:199-229`).
- Root router: `shared/presentation/api/root_router.py` — per-context routers
  mounted under `/api/<prefix>` (lines 39-58). AGENTS.md rule 10: never add
  routes in `entrypoints/api.py`.
- Test client: `tests/conftest.py::client` builds a fresh FastAPI app with
  `api_router` and overrides ALL factories including the three candidate repos
  (lines 171-173). Per-context API conftest example:
  `tests/jobs/presentation/api/conftest.py`.
- Frontend FSD: no `candidate` slice exists. Blueprint to copy:
  `entities/company/*`, `features/companies-v2/*`, `widgets/companies-page/*`,
  `app/companies/page.tsx`, nav in `widgets/header/nav-items.ts`. API client
  `shared/api/http-client.ts` (`api.get/post/...`, base `/api`). UI kit in
  `shared/ui/` + shared components (`ConfirmDialog`, `ProcessingDrawer`,
  `PageHeader`, ...). Resume upload = paste-text into `Textarea` (see
  `features/resume/components/ResumeTab.tsx`).
- UX docs: `docs/ux/features/`, `docs/ux/flows/`, index `docs/ux/README.md`,
  master wireframes `DESIGN.md` (root). Rule 13 requires ASCII wireframes +
  Mermaid for new UI.

## Scope (this phase)

### 1. Backend — `apps/backend/candidates/presentation/` (new)

- `api/candidates_router.py` + `api/schemas/candidates.py`:
  - `GET /profile` → current profile dict (all children) or `404` if none.
  - `GET /sources` → `{"items": [...]}` from `list_for_profile` (newest first).
  - `GET /versions` → `{"items": [...]}` from `list_versions` (newest first).
  - `POST /analyze` (202) → create + dispatch a `CANDIDATE_PROCESSING`
    execution (`target_type="candidate"`), returns
    `{"execution_id": ..., "status": "queued"}`.
- Register in `root_router.py`: import `candidates.presentation.api.candidates_router`
  as `candidates_router`, mount `api_router.include_router(candidates_router,
  prefix="/candidates", tags=["candidates"])`.
- Conventions: typed `Depends(get_candidate_profile_repo)` etc., Pydantic
  response schemas, `NotFoundError` from `shared.application.exceptions`.
- Tests (TDD): `tests/candidates/presentation/api/test_candidates_router.py`
  using the shared `client` fixture (profile present/absent, sources, versions,
  analyze dispatch via patched dispatch). No per-context conftest needed since
  `tests/conftest.py::client` already overrides the candidate repos.

### 2. Frontend — FSD (all new under `apps/frontend/src/`)

- `entities/candidate/types.ts` — CandidateProfile, CandidateSkill,
  CandidateExperience, CandidateProject, CandidateSource, CandidateVersion
  interfaces matching the backend dicts.
- `entities/candidate/api.ts` — `candidateApi.getProfile/getSources/getVersions/analyze`.
- `entities/candidate/hooks.ts` — `useCandidateProfileQuery`,
  `useCandidateSourcesQuery`, `useCandidateVersionsQuery`,
  `useAnalyzeProfileMutation`.
- `features/candidate-v2/components/ProfileImportPage.tsx` — three-step flow:
  - **Sources**: resume upload (paste text → POST `/api/resumes`), LinkedIn
    paste (POST `/api/linkedin`), GitHub username (optional, placeholder).
  - **Analyze**: button → `POST /api/candidates/analyze`; show SSE progress via
    `useProcessingEvents` (reuse `ProcessingDrawer` / `WorkflowTerminal` style).
  - **Review**: after processing, fetch profile + sources + versions; render
    skills (level/confidence/evidence), experience, projects, sources, summary;
    Confirm / Cancel. Confirm = toast + keep page (post-hoc model).
  - Loading / empty / error states per repo conventions.
- `widgets/candidate-page/index.tsx` (adapter + `<MainLayout>`, mirror
  `widgets/companies-page/index.tsx`) + `app/candidate/page.tsx` (dynamic import,
  `ssr: false`).
- Nav item `candidate` ("Candidate", route `/candidate`) in
  `widgets/header/nav-items.ts`.
- Tests (vitest): `entities/candidate/hooks.test.ts` (or api test) + a
  `ProfileImportPage.test.tsx` render/interaction test.

### 3. Docs (rule 13)

- `docs/ux/features/candidate/profile-import.md` — purpose, ASCII wireframe,
  Mermaid component/state diagram, states, actions, component hierarchy.
- `docs/ux/flows/candidate/import-profile.md` — user journey ASCII + Mermaid.
- Update `docs/ux/README.md` index tree + `DESIGN.md` (nav tree + wireframe
  section entry).
- Note: these are the first UX docs to include Mermaid (rule 13 gap).
- `implementation-history/103_candidate_profile_import.md` (this file).

## Out of Scope (later phases)

- Dashboard, Sources/Skills/Experience/Projects pages, Gap Analysis (110 P2-7).
- Roadmap replacement + removal of legacy `skill_roadmaps` (110 Phase 8).
- GitHub adapter implementation (stub only).

## Testing Requirements

- Backend: `uv run pytest apps/backend/tests/candidates/ -v` + full suite
  `uv run pytest apps/backend/tests/ -v` (>= current count), ruff clean.
- Frontend: `cd apps/frontend && npx vitest run && npm run lint && npm run typecheck`.

## Implementation Notes (verification results)

- Backend: full suite **1486 passed** (1479 + 7 new candidates router tests).
  Ruff clean on all new candidates files. Note: `ruff check` on
  `shared/presentation/api/root_router.py` reports 10 pre-existing errors
  (unused imports / E402 for existing v2 router imports) — none from this change.
- Frontend: full vitest suite **468 passed** (463 + 5 new candidate hooks tests).
  `npm run typecheck` passes for all new candidate/linkedin files; the command
  still reports pre-existing errors in other files (`MultiSelect.test.tsx`,
  `shared/lib/skills.ts`, `features/resume/...`, `widgets/resume-page/...`).
- `npm run lint` (`next lint`) is **broken pre-existing**: no ESLint config
  exists and Next 16 removed `next lint`, so it fails with
  `Invalid project directory ... no such directory: apps/frontend/lint`. Not
  introduced by this change; typecheck + vitest are the gate for new code.
- Docs delivered: `docs/ux/features/candidate/profile-import.md`,
  `docs/ux/flows/candidate/import-profile.md` (first UX docs with Mermaid),
  `docs/ux/README.md` index + `DESIGN.md` nav/wireframe entries. No new domain
  events in this phase — `docs/domain/candidates/events.md` already documents
  the candidate pipeline events.

## Constraints

- No DB changes / migrations. No new LLM calls.
- Reuse existing resume/linkedin endpoints for source ingestion; no new
  source-storage endpoint.
- Keep candidates context presentation layer self-contained (rules 10/15/16).
