# Prompt 146 - Roadmap AI Generation + Remove Legacy Application Preparation

## Objective

Two coupled backend changes:

1. **AI roadmap generation**: generate a Roadmap from an Application by reusing
   existing Job/Company/User/Skill-gap intelligence (spec `144_feature_roadmap.md`
   §13–§14, MVP §48). One LangGraph workflow, one LLM call, persisted into the
   Roadmaps context created in prompt 145.
2. **Remove the legacy Application preparation plan completely** (backend side;
   frontend removal is 147). It is replaced by the AI-generated roadmap, so its
   table, repo, entity, event, prompt/schema/validation, endpoint and execution type
   are deleted.

## Current State

### Legacy preparation (to remove)

- Table `application_preparations` in schema `application`
  (`apps/backend/applications/infrastructure/models/application_model.py:71-82`;
  migration `apps/alembic/application/versions/application_001_initial_application_schema.py`).
- Domain entity `ApplicationPreparation` (`applications/domain/entities/application.py:128-149`).
- Repo port `IPreparationRepository` (`applications/domain/repositories/preparation_repository.py`)
  + impl `SQLAlchemyPreparationRepository` (`applications/infrastructure/repositories/sa_preparation_repository.py`,
  exported by `applications/infrastructure/__init__.py:13`, wired in
  `apps/backend/dependencies.py:154-156` `get_preparation_repo`).
- Event `ApplicationPreparationGenerated` (`applications/domain/events.py:65-71`).
- Schemas `HardSkillRecommendationSchema`, `SoftSkillRecommendationSchema`,
  `ApplicationPreparationSchema`, `build_preparation_schema`, `preparation` field on
  `ApplicationDetailResponse` + `build_detail_response` arg
  (`applications/presentation/api/schemas/applications.py:74-101,113,126-138,141-157`).
- Endpoint `POST /api/applications/{id}/preparation/generate`
  (`applications/presentation/api/applications_router.py:186-195`); `preparation_repo`
  params in `_detail` (66-81) and detail-building handlers (96-151).
- Processing: `ExecutionType.APPLICATION_PREPARATION`
  (`processing/domain/enums.py:13`), prep branch in
  `processing/application/workflows/application_intelligence/`:
  `build_preparation_output_schema` + `build_preparation_prompt`
  (`processing/application/services/application_intelligence_prompts.py:23-57,79-103`),
  `PreparationOutput`/`HardSkillPlan`/`SoftSkillPlan`
  (`application_intelligence_validation.py:29-110`), `_persist_preparation`
  (`nodes/persist_node.py:60-83`), prep intent in `_plan_for`
  (`nodes/generate_node.py:94-102`), `preparation_repo` wiring in `graph.py` and
  `processing/infrastructure/workflow/assembly.py:172` (`build_application_intelligence_graph`).

### Roadmap context (from prompt 145, to exist)

- `apps/backend/roadmaps/` context: `IRoadmapRepository`/`SQLAlchemyRoadmapRepository`,
  `RoadmapService`, entities (`Roadmap`, `RoadmapGoal`, `RoadmapMilestone`,
  `RoadmapTask`, `RoadmapSkillLink`, `RoadmapNote`, `RoadmapResource`),
  `RoadmapEventPublisher`/`InMemoryEventCollector`, router + schemas.

### Reusable AI building blocks

- `LLMService.generate_structured(prompt, schema, timeout)` — `ai/infrastructure/service.py:84`;
  singleton `get_llm_service()` (`:193`).
- Application intelligence inputs — `processing/application/services/application_intelligence_inputs.py`:
  `build_application_context(...)` (`:136`) returns `{job, job_skills, company, candidate}`.
- LangGraph template — `processing/application/workflows/application_intelligence/graph.py`
  (StateGraph, nodes, conditional edges), state
  `processing/domain/workflow/application_intelligence_state.py`.
- Execution pipeline: `CreateProcessingExecutionUseCase` + `DispatchProcessingExecutionService`
  (`processing/application/use_cases/create_processing_execution.py`,
  `processing/application/services/dispatch_processing_execution.py`), runner branch in
  `processing/infrastructure/runner/execution_runner.py:245-282`, graph wiring in
  `processing/infrastructure/workflow/assembly.py:156-176`, SSE progress via
  `progress_ops` + per-workflow step mappers (`application_workflow_step_mapper.py:46`).
- Skill find-or-create: `SQLAlchemySkillRepository.resolve_skill` (`skills/infrastructure/repositories/sa_skill_repository.py:529`).

## Changes

### A. New roadmap generation workflow

New directory `apps/backend/processing/application/workflows/roadmap_generation/`:

1. **State** — `processing/domain/workflow/roadmap_generation_state.py`
   (`RoadmapGenerationState`): `execution_id`, `application_id`, `job_id`, `intent`,
   `context`, `result`, `persisted_roadmap_id`, `errors`, `workflow_progress`, `status`
   (mirror `application_intelligence_state.py:30`).
2. **Graph** — `graph.py` `RoadmapGenerationGraph` (StateGraph):
   `load_context → generate → persist → roadmap_ready | execution_failed`.
3. **Nodes**:
   - `load_context_node.py`: loads application (`application_repo.get_by_id`), its
     `job_id`, job, job analysis, company, company intelligence, candidate profile
     (reuse the same repositories `build_application_intelligence_graph` wires at
     `assembly.py:162-173`), then `build_application_context(...)`.
   - `generate_node.py`: one `llm.generate_structured(roadmap_prompt, schema, timeout=240)`
     (mirror `generate_node.py:71-133` incl. one retry on schema failure). Adds
     `prompt_version`/`schema_version` from the prompts module.
   - `persist_node.py`: writes the roadmap via `SQLAlchemyRoadmapRepository` +
     `RoadmapService`:
     - `Roadmap` source=`APPLICATION`, `application_id`, `goal_type=JOB`, status ACTIVE.
     - `RoadmapGoal` type=`JOB`, title from AI, `target_job_id=job_id`,
       `target_company_id` from job's company link if present.
     - Milestones + Tasks in AI order (position 0..n), each `RoadmapTask`'s status
       NOT_STARTED.
     - Skills: for each AI `skill` name, `skill_repo.resolve_skill(...)` and create a
       `RoadmapSkillLink` on the milestone (and task-level when the AI nests them).
     - Emit `RoadmapCreated` (via service) and `RoadmapGenerated`-equivalent events
       through `RoadmapEventPublisher`.
     - Store `persisted_roadmap_id` in state.
   - `roadmap_ready_node.py` / `execution_failed_node.py`: terminal nodes mirroring
     `application_ready_node.py` / `execution_failed_node.py`.
4. **Step mapper** — `processing/application/workflows/roadmap_workflow_step_mapper.py`:
   steps `Load Context → Generate → Save Result` (mirror
   `application_workflow_step_mapper.py:46`).
5. **Inputs / prompts / validation** — `processing/application/services/roadmap_generation_*`:
   - `roadmap_generation_prompts.py`: `ROADMAP_GENERATION_PROMPT_VERSION = "1.0.0"`,
     `build_roadmap_output_schema()` (title, goal{type,title,description}, milestones[
       {title, description, priority, success_criteria, skills[], tasks[{title, description,
       estimated_effort, success_criteria}]}] — required milestones), and
     `build_roadmap_prompt(context)` grounded in `["job", "job_skills", "company", "candidate"]`.
     Rules mirror spec §14: actionable milestones (outcomes, not bare topics), concrete
     tasks, ≤8 milestones × ≤8 tasks, prioritize smallest meaningful gap set (§15).
   - `roadmap_generation_validation.py`: Pydantic `RoadmapOutput`/`MilestonePlan`/
     `TaskPlan` with `dump_payload()` (mirror `application_intelligence_validation.py:82-110`);
     enforce priority ∈ {critical, high, medium, low} and status/type enums.
6. **Execution plumbing**:
   - `processing/domain/enums.py`: add `ROADMAP_GENERATION = "roadmap_generation"`.
   - `processing/infrastructure/runner/execution_runner.py`: add branch for
     `ExecutionType.ROADMAP_GENERATION` building
     `build_roadmap_generation_graph(graph_session)` and invoking with
     `RoadmapGenerationState(execution_id=..., application_id=target_id, job_id="", intent=..., workflow_progress=build_initial_progress(...))`.
   - `processing/infrastructure/workflow/assembly.py`: add
     `build_roadmap_generation_graph(session)` wiring `SQLAlchemyApplicationRepository`,
     `JobService`, `SQLAlchemyJobAnalysisRepository`, `CompanyService`,
     `SQLAlchemyCompanyIntelligenceRepository`, `SQLAlchemyCandidateProfileRepository`,
     `SQLAlchemyRoadmapRepository`, `SQLAlchemySkillRepository`, `get_llm_service()`,
     `RedisProcessingEventPublisher`, `InMemoryEventCollector` (or `RoadmapEventPublisher`).
   - Wire the `roadmap_generation` step mapper into the workflow-progress builder for
     `target_type="application"` / this execution type (`progress_ops._build_initial_progress`).
7. **API endpoint** — in `applications/presentation/api/applications_router.py` add:
   `POST /api/applications/{application_id}/roadmap/generate` → 202 `GenerateResponse(
   execution_id=..., status="queued", artifact="roadmap")`, dispatching
   `ExecutionType.ROADMAP_GENERATION` via the existing `_dispatch` helper (`:84-93`).

### B. Remove legacy preparation (backend)

- **Migration**: new `apps/alembic/application/versions/application_002_drop_preparation.py`
  (autogenerate after deleting the model) dropping `application_preparations` + its
  index. Verify `uv run alembic upgrade head` + downgrade round-trip.
- **Applications context**:
  - Delete `applications/domain/entities/application.py:128-149` +
    `ApplicationPreparation` from `__all__` (`:152-159`).
  - Delete `applications/domain/repositories/preparation_repository.py`,
    `applications/infrastructure/repositories/sa_preparation_repository.py`,
    mappers `preparation_model_to_dict`/`dict_to_preparation_model`
    (`applications/infrastructure/mappers.py:98-115`), model
    `ApplicationPreparationModel` (`application_model.py:71-82`), lazy export
    `applications/infrastructure/__init__.py:13`.
  - Remove event `ApplicationPreparationGenerated` (`domain/events.py:65-71`).
  - Remove `get_preparation_repo` (`dependencies.py:154-156`).
  - Schemas: remove `HardSkillRecommendationSchema`, `SoftSkillRecommendationSchema`,
    `ApplicationPreparationSchema`, `build_preparation_schema`, `preparation` field and
    `preparation_repo` params/args across `applications_router.py` + `schemas/applications.py`.
  - Remove `POST /{application_id}/preparation/generate` (`applications_router.py:186-195`).
- **Processing context**:
  - Remove `ExecutionType.APPLICATION_PREPARATION` (`processing/domain/enums.py:13`).
  - Remove prep prompt/schema (`application_intelligence_prompts.py:23-57,79-103`),
    prep validation models (`application_intelligence_validation.py:29-110` — keep
    `DocumentOutput`), `_persist_preparation` (`persist_node.py:60-83`), prep intent
    from `_plan_for` (`generate_node.py:94-102`), `preparation_repo` param/wiring in
    `graph.py` + `assembly.py:172`.
- **Docs**: update `docs/domain/applications/events.md` (remove
  `application.preparation.generated`), `docs/ai/application-intelligence.md`
  (prepare→roadmap), `docs/ux/features/applications/preparation-plan.md` and
  `docs/ux/flows/applications/generate-application-artifacts.md` will be handled by
  prompt 147 (frontend) — coordinate so no doc references the removed artifact.
- **Tests**: update `apps/backend/tests/applications/presentation/api/test_applications_router.py`
  (prep tests at 207-213, 248, 253-272) and
  `apps/backend/tests/applications/domain/test_application_services.py` (183, 365-370)
  to drop prep coverage and assert the roadmap endpoint instead.

## Testing Requirements

Backend:

- New `apps/backend/tests/processing/.../test_roadmap_generation_*`:
  - prompts/validation: schema shape, priority enum, dump_payload round-trip.
  - persist node: creates roadmap+goal+milestones+tasks+skill links via
    `resolve_skill`, sets source/application_id, emits `RoadmapCreated` +
    `roadmap.milestone.added`/`roadmap.task.added` events (collector).
  - graph end-to-end with `MockProvider`: application context loaded, one LLM call,
    execution COMPLETED, `persisted_roadmap_id` set.
  - router: `POST /api/applications/{id}/roadmap/generate` returns 202 +
    `artifact="roadmap"`; 404 for unknown application.
- Regression: applications router/service tests updated (prep removal), full suite green.

Run: `uv run pytest apps/backend/tests/ -v`.

## Constraints

- All AI via `LLMService` (rule 1); one structured call per generation.
- Reuse existing intelligence — do not re-analyze raw job/company/profile text
  (spec §13).
- Roadmap is an independent entity; generation only persists into the roadmaps context.
- No cross-context FKs (skill links are logical). No raw SQL.
- Migrations autogenerated first, then tuned (rule 14).
- Do NOT touch the frontend here (147) beyond leaving the `GenerateResponse.artifact`
  contract `"roadmap"` documented.