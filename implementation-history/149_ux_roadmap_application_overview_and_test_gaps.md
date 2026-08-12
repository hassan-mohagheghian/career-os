# Prompt 149 - Roadmap Application Overview + Close Test Gaps

## Objective

Close the audit gaps from prompts 146/147 (missing backend `test_roadmap_generation_*`
suite, missing `GenerationProgress` roadmap-label test, missing `entities/roadmap/hooks`
tests) and add a **Roadmap Overview** to the Application Workspace: when an application
has a generated roadmap, its ROADMAP section shows a brief overview (title, goal, overall
progress **and each milestone's status/priority/task-count/progress**) instead of only a
compact progress card. Docs-first with ASCII wireframes + Mermaid.

## Current State

- Roadmap generation backend is complete (prompt 146): `RoadmapGenerationGraph` with 5
  nodes in `apps/backend/processing/application/workflows/roadmap_generation/`, prompts +
  validation in `apps/backend/processing/application/services/roadmap_generation_{prompts,validation}.py`,
  state in `apps/backend/processing/domain/workflow/roadmap_generation_state.py`, step
  mapper + `progress_ops` dispatch, `assembly.build_roadmap_generation_graph`, runner branch
  (`execution_runner.py:283`). No `apps/backend/tests/processing/application/test_roadmap_generation_*`
  exists (router 202/404 already covered in `test_applications_router.py`).
- Frontend workspace `ROADMAP` section (prompt 147) = `RoadmapSection.tsx`
  (`apps/frontend/src/features/job-application/components/RoadmapSection.tsx`) which shows
  only a compact `RoadmapReadyCard` (title/goal/badge/progress bar + View/Regenerate/Delete)
  when `useRoadmapByApplicationQuery` resolves. `RoadmapDetail` (`entities/roadmap/types.ts`) already
  carries `milestones[].{position,status,priority,tasks,skills}` and `progress.milestone_progress`.
- `GenerationProgress.tsx` has `artifactLabels.roadmap` but `GenerationProgress.test.tsx`
  has no roadmap-label case. `entities/roadmap/hooks.ts` (query keys `['roadmap','list']`,
  `['roadmap', id]`, `['roadmap','by-application', appId]` + invalidation) has **no hooks test**
  (only `api.test.ts`; precedent: `entities/candidate/hooks.test.tsx`).
- Version is still `3.13.0` (VERSION, CHANGELOG.md top, pyproject.toml, apps/frontend/package.json).

## Changes

### Backend tests (prompt 146 gap)

New `apps/backend/tests/processing/application/test_roadmap_generation.py` (model after
`test_application_intelligence.py`):
- Fakes: `_job/_analysis/_company/_intelligence/_profile` builders, `FakeApplicationRepo`,
  `FakeJobService`, `FakeAnalysisRepo`, `FakeCompanyService`, `FakeIntelligenceRepo`,
  `FakeProfileRepo`, `FakeLLM` (content/error + calls), `RecordingEventPublisher` and a
  `FakeRoadmapService` reusing `InMemoryEventCollector`-compatible collector asserting domain events.
- `TestPrompts`: schema shape, priority enum values, `RoadmapOutput.dump_payload` round-trip.
- `TestValidation`: `RoadmapOutput` accepts valid payload, rejects missing/empty milestones,
  invalid priority.
- `TestLoadContextNode`: loads context + fails when application/job missing (mirror intelligence).
- `TestGenerateNode`: valid payload accepted (title/goal/milestones/tasks), schema-invalid
  payload fails clean (`does not match the required format`), LLM error fails, retry-once path.
- `TestPersistNode`: with `FakeRoadmapService` + `FakeSkillRepo.resolve_skill`, asserts roadmap
  created (source=APPLICATION, application_id), milestone + tasks created with priorities mapped
  to uppercase, skill links resolved, and domain events emitted (`RoadmapCreated`,
  `roadmap.milestone.added`, `roadmap.task.added`, `roadmap.skill.linked`) via collector.
- `TestGraphE2E`: `RoadmapGenerationGraph.invoke` with all fakes + `FakeLLM` returns COMPLETED,
  `persisted_roadmap_id` set, one LLM call; failure routes to `execution_failed`.
- `TestStepMapper`: `RoadmapWorkflowStepMapper` node→step mapping, displayable flags,
  `build_initial_progress` ids == `["load_context","generate","persist"]`; `progress_ops`
  dispatch for `intent=="roadmap_generation"`.

### Frontend tests (prompt 147 gaps)

- `GenerationProgress.test.tsx`: add `roadmap` artifact → label "Learning roadmap".
- New `apps/frontend/src/entities/roadmap/hooks.test.tsx` (model after
  `entities/candidate/hooks.test.tsx`): mock `./api`; assert `useRoadmapsQuery`,
  `useRoadmapQuery(id)`, `useRoadmapByApplicationQuery(applicationId)` query keys + payloads;
  assert `useCreateRoadmapMutation`/`useUpdateRoadmapMutation`/`useDeleteRoadmapMutation`/
  `useLinkSkillMutation` call the right api fn and invalidate queries (spy `queryClient.invalidateQueries`).

### Roadmap Overview (new UX)

- `RoadmapSection.tsx`: when a roadmap exists, render `RoadmapReadyCard` (keep) **plus** a new
  `RoadmapOverview` list: for each `milestone` (sorted by position) show index badge, title,
  status badge, priority badge, `done/total` + mini `Progress` bar (percent computed from tasks).
  Keep View map button. No new endpoints needed (data already in `RoadmapDetail`).
- `ApplicationWorkspace.test.tsx`: extend roadmap-ready fixture with 1–2 milestones + tasks and
  assert milestone titles/status/priority and per-milestone counts render in the ROADMAP section.

### Docs (rule 13)

- New `docs/ux/features/roadmaps/roadmap-application-overview.md` with ASCII wireframe of the
  ROADMAP section overview states (empty / without roadmap / with roadmap overview) + Mermaid
  (data flow: workspace → `GET /api/roadmaps/by-application/{id}` → RoadmapOverview).
- Update `docs/ux/features/applications/workspace.md` ROADMAP block + component hierarchy +
  behaviors to mention milestone overview.
- Update `docs/ux/features/roadmaps/roadmap-generation.md` ready-state card to include overview.
- Update `docs/ux/README.md` index + `docs/ux/DESIGN.md` roadmap wireframe block.

### Release (version sync, given rule 12)

- Bump to `3.14.0` in `VERSION` (source of truth), `CHANGELOG.md` (new `## [3.14.0]` entry at
  top summarizing roadmap generation + workspace overview), `pyproject.toml`, `apps/frontend/package.json`.
- `./scripts/check-version.sh` must pass (run without `--tag`).

## Testing Requirements

- Backend: `uv run pytest apps/backend/tests/processing/application/test_roadmap_generation.py -v`
  plus full `uv run pytest apps/backend/tests/ -v`.
- Frontend: `cd apps/frontend && npx vitest run` plus `npm run lint` and `npm run typecheck`.
- Version: `./scripts/check-version.sh`.

## Constraints

- All AI via `LLMService` (rule 1); tests use fake LLM only (no provider).
- No cross-context FKs (rule 15) — skill links logical; `FakeSkillRepo.resolve_skill` mirrors port.
- Docs-first (rule 13): wireframes + Mermaid committed with the UI change.
- No raw SQL; no `print()` (structlog).
- Overview is read-only in the workspace; editing stays in the Roadmap detail page.