# Prompt 145 - Roadmap Backend Domain (MVP, no AI)

## Objective

Introduce a new **Roadmaps** bounded context as an independent domain entity
(spec `144_feature_roadmap.md`, MVP scope §48). Backend only: data model,
repositories, services, CRUD API and progress calculation. No AI in this prompt
(that is prompt 146). The legacy Application **preparation plan** is untouched
here and fully removed in prompt 146/147.

## Current State

- No roadmap code exists in the backend. Frontend has no roadmap code either.
- Existing bounded-context template to mirror: `apps/backend/applications/`
  (entities in `domain/entities/`, ABC ports in `domain/repositories/`, SQLAlchemy
  models in `infrastructure/models/`, mappers, lazy facade `infrastructure/__init__.py`,
  per-context router in `presentation/api/`, schemas next to it).
- DB access uses SQLAlchemy ORM; schemas are per context via
  `apps/backend/shared/infrastructure/database/sqlalchemy_config.py` (`Base` +
  `__table_args__ = {"schema": "..."}`). Migrations live in
  `apps/alembic/<context>/versions/` (currently `job`, `company`, `skill`, `shared`,
  `candidate`, `application`). `alembic.ini` has `version_locations` listing them.
- Id generation uses `uuid.uuid7()` (see `applications/domain/entities/application.py:64`).
- Cross-context links are plain indexed columns, never FKs (AGENTS.md rule 15);
  within-context FKs are fine. Example: `applications.job_id` is FK-free
  (`applications/infrastructure/models/application_model.py:32`).
- Router registration: `apps/backend/shared/presentation/api/root_router.py`
  (api_router prefix `/api`, line 29; per-context include at line 52).
- DI: per-context repo factories in `apps/backend/dependencies.py`.
- Domain events: frozen dataclasses over `shared/domain/domain_event.py`, documented
  in `docs/domain/<context>/events.md` (see `docs/domain/applications/events.md`),
  in-memory collector port (rule 16).
- Skill entity is global: `apps/backend/skills/infrastructure/repositories/sa_skill_repository.py`
  `resolve_skill` (line 529) finds-or-creates by name/alias/slug and returns an id —
  use it to attach skills (logical `skill_id`, no FK).

## Changes

### 1. Domain entities — `apps/backend/roadmaps/domain/entities/roadmap.py`

Dataclasses (timestamps + `to_dict`, mirroring `applications` context):

- Constants:
  - `RoadmapSource`: `APPLICATION`, `AI_GENERATED`, `MANUAL`.
  - `RoadmapStatus`: `ACTIVE`, `COMPLETED`, `ARCHIVED`.
  - `GoalType`: `JOB`, `CAREER`, `SKILL`, `CUSTOM` (JOB is what generation uses).
  - `NodePriority`: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
  - `TaskStatus`: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `SKIPPED`.
  - `MilestoneStatus`: same values as `TaskStatus`.
  - `ResourceType`: `ARTICLE`, `VIDEO`, `COURSE`, `BOOK`, `DOCUMENTATION`, `PROJECT`, `OTHER`.
  - `ResourceStatus`: `PLANNED`, `IN_PROGRESS`, `COMPLETED`.
  - `ResourceSource`: `AI`, `USER`.
- `Roadmap` (aggregate root): `id`, `title`, `description`, `goal_type` (default
  `CUSTOM`), `source` (default `MANUAL`), `application_id` (str|None — logical ref,
  no FK), `status` (default `ACTIVE`), timestamps.
- `RoadmapGoal` (1-1 child, plain table for future target links): `id`,
  `roadmap_id`, `type` (GoalType), `title`, `description`, `target_job_id`|None,
  `target_company_id`|None, `target_skill_id`|None, timestamps.
- `RoadmapMilestone`: `id`, `roadmap_id`, `position` (int), `title`, `description`,
  `status` (default NOT_STARTED), `priority` (default MEDIUM), timestamps.
- `RoadmapTask`: `id`, `milestone_id`, `position`, `title`, `description`, `status`
  (default NOT_STARTED), `priority`, `estimated_effort` (str|None), `success_criteria`
  (str|None), `completed_at` (str|None), timestamps.
- `RoadmapSkillLink`: `id`, `roadmap_id`, `milestone_id`|None, `task_id`|None,
  `skill_id` (str, logical ref — **no FK**), `position`, timestamps.
- `RoadmapNote`: `id`, `roadmap_id`, `milestone_id`|None, `task_id`|None, `content`,
  timestamps.
- `RoadmapResource`: `id`, `roadmap_id`, `milestone_id`|None, `task_id`|None, `title`,
  `url`, `description`, `type` (ResourceType), `status` (ResourceStatus),
  `source` (ResourceSource, default USER), timestamps.

### 2. Domain events — `apps/backend/roadmaps/domain/events.py`

Frozen dataclasses over `DomainEvent` (§ pattern of `applications/domain/events.py`):

- `RoadmapCreated` → `roadmap.created` (payload: roadmap_id, source, application_id?)
- `RoadmapUpdated` → `roadmap.updated`
- `RoadmapDeleted` → `roadmap.deleted`
- `RoadmapMilestoneAdded` → `roadmap.milestone.added`
- `RoadmapMilestoneUpdated` → `roadmap.milestone.updated`
- `RoadmapMilestoneDeleted` → `roadmap.milestone.deleted`
- `RoadmapTaskAdded` → `roadmap.task.added`
- `RoadmapTaskUpdated` → `roadmap.task.updated` (also fired on status change → progress)
- `RoadmapTaskDeleted` → `roadmap.task.deleted`
- `RoadmapNoteAdded` → `roadmap.note.added`
- `RoadmapResourceAdded` → `roadmap.resource.added`
- `RoadmapSkillLinked` → `roadmap.skill.linked`

Add `apps/backend/roadmaps/domain/event_publisher.py`:
`RoadmapEventPublisher` ABC + `InMemoryEventCollector` (copy of
`applications/domain/event_publisher.py`).

Document catalog at `docs/domain/roadmaps/events.md` (trigger/payload/fires/consumers;
consumers: none).

### 3. Repository ports — `apps/backend/roadmaps/domain/repositories/roadmap_repository.py`

`IRoadmapRepository` ABC with: `get_by_id`, `get_by_application_id`,
`list` (newest first, `created_at desc` — rule 7), `create`, `update`, `delete`,
`delete_by_application`, plus typed child accessors: `list_milestones(roadmap_id)`
(by position), `create_milestone`, `update_milestone`, `delete_milestone`,
`list_tasks(milestone_id)`, `create_task`, `update_task`, `delete_task`,
`list_skills_for_roadmap`, `create_skill_link`, `delete_skill_link`,
`list_notes`, `create_note`, `delete_note`, `list_resources`, `create_resource`,
`update_resource`, `delete_resource`.

### 4. SQLAlchemy models — `apps/backend/roadmaps/infrastructure/models/roadmap_model.py`

One model per entity above, schema `roadmap`, `id = String(36)` default uuid7.
Within-context FKs: `roadmap_goals.roadmap_id`, `roadmap_milestones.roadmap_id`,
`roadmap_tasks.milestone_id`, `roadmap_skill_links.{roadmap_id,milestone_id,task_id}`,
`roadmap_notes.{roadmap_id,milestone_id,task_id}`,
`roadmap_resources.{roadmap_id,milestone_id,task_id}` → `roadmap.roadmaps.id`
**only** (milestone/task columns too, since children of those rows — rule 15 only
bans cross-context FKs). `roadmap_skill_links.skill_id` is a plain indexed column
(no FK — skill is a different context). Index `roadmaps.application_id`.

### 5. Repositories + mappers

- `apps/backend/roadmaps/infrastructure/mappers.py` — model ↔ dict mappers for every
  entity.
- `apps/backend/roadmaps/infrastructure/repositories/sa_roadmap_repository.py` —
  `SQLAlchemyRoadmapRepository(IRoadmapRepository)`. Cascade deletes manually within
  context (delete skills/notes/resources/tasks/milestones/goal then roadmap —
  mirror `sa_application_repository.py:71-83`). Commit per operation.
- `apps/backend/roadmaps/infrastructure/__init__.py` — lazy facade exporting
  `SQLAlchemyRoadmapRepository`.

### 6. Services — `apps/backend/roadmaps/application/services/roadmap_service.py`

`RoadmapService` (constructor: `roadmap_repo`, optional `RoadmapEventPublisher`
defaulting to `InMemoryEventCollector`):

- `create_manual(title, description, goal: RoadmapGoal|None)` → source=MANUAL,
  creates roadmap + goal, emits `RoadmapCreated`.
- `get(roadmap_id)`, `list()`, `update(roadmap_id, data)` (title/description/status/
  goal fields; emits `RoadmapUpdated`).
- `delete(roadmap_id)` (emits `RoadmapDeleted`); `delete_by_application(application_id)`.
- `add_milestone(roadmap_id, ...)`, `update_milestone`, `delete_milestone` (emits
  milestone events; positions managed by appending as needed).
- `add_task(milestone_id, ...)`, `update_task` (accepts status → sets `completed_at`
  when `COMPLETED`), `delete_task` (emits task events).
- `add_note`/`delete_note`, `add_resource`/`update_resource`/`delete_resource`,
  `link_skill(milestone_id|task_id, skill_id)`.
- Progress: computed, not stored — `compute_progress(roadmap_id) -> dict`:
  `{completed_tasks, total_tasks, milestone_progress: [{milestone_id, completed, total, percent}], overall_percent}`.
  overall_percent = completed tasks / total tasks (0 when no tasks). Files emit
  `RoadmapTaskUpdated` is up to `update_task`.

### 7. API — `apps/backend/roadmaps/presentation/api/roadmaps_router.py` + schemas

`roadmaps_router.py` (router prefix registered in root_router as `/roadmaps`):

- `POST /api/roadmaps` (source=MANUAL; body: title, description, goal) → 201 `RoadmapDetailResponse`.
- `GET /api/roadmaps` → list (summaries with progress).
- `GET /api/roadmaps/by-application/{application_id}` → roadmap detail or 404.
- `GET /api/roadmaps/{roadmap_id}` → detail (goal, milestones+skills, tasks w/ skills,
  notes, resources, progress).
- `PATCH /api/roadmaps/{roadmap_id}` (title/description/status/goal).
- `DELETE /api/roadmaps/{roadmap_id}` → `DeleteResponse`.
- `POST /api/roadmaps/{roadmap_id}/milestones` → 201.
- `PATCH /api/roadmaps/milestones/{milestone_id}` (`position` reorder, status, title,
  description, priority).
- `DELETE /api/roadmaps/milestones/{milestone_id}`.
- `POST /api/roadmaps/milestones/{milestone_id}/tasks` → 201.
- `PATCH /api/roadmaps/tasks/{task_id}` (`position`, status → progress recomputed,
  title, description, priority, estimated_effort, success_criteria).
- `DELETE /api/roadmaps/tasks/{task_id}`.
- `POST /api/roadmaps/{roadmap_id}/notes` (body: milestone_id|task_id, content) → 201.
- `DELETE /api/roadmaps/notes/{note_id}`.
- `POST /api/roadmaps/{roadmap_id}/resources` → 201 (title, url, type, status,
  milestone_id|task_id).
- `PATCH /api/roadmaps/resources/{resource_id}`; `DELETE /api/roadmaps/resources/{resource_id}`.
- `POST /api/roadmaps/skills` (body: milestone_id|task_id, skill_name) → resolves via
  `SQLAlchemySkillRepository.resolve_skill` and links; returns `{skill_id, name}`.
- `DELETE /api/roadmaps/skills/{link_id}`.

`schemas/roadmaps.py`: request/response Pydantic models +
`build_roadmap_summary`, `build_roadmap_detail` helpers. Include `roadmaps_router`
in `apps/backend/shared/presentation/api/root_router.py` (prefix `/roadmaps`,
tags `["roadmaps"]`).

### 8. DI — `apps/backend/dependencies.py`

Add `get_roadmap_repo` (session → `SQLAlchemyRoadmapRepository`) and
`get_roadmap_service` (repo + `InMemoryEventCollector`).

### 9. Migration (AGENTS.md rule 14 — autogenerate first)

1. Add `apps/alembic/roadmap/versions` to `version_locations` in `alembic.ini`.
2. From repo root run:
   `ALEMBIC_TARGET_SCHEMA=roadmap uv run alembic revision --autogenerate -m "roadmap: initial roadmap schema" --version-path apps/alembic/roadmap/versions --branch-label roadmap`
3. Tune generated file (rename to `roadmap_001_initial_roadmap_schema.py`, add
   `CREATE SCHEMA IF NOT EXISTS roadmap`, FKs, indexes). Verify
   `uv run alembic history`, `uv run alembic heads` (multi-head OK — new branch),
   `uv run alembic upgrade head`, and a downgrade/upgrade round-trip.

### 10. Domain docs

- `docs/domain/roadmaps/roadmap.md` — entity model, statuses, sources, progress math.
- `docs/domain/roadmaps/events.md` — event catalog (rule 16).

## Testing Requirements

Backend (`apps/backend/tests/roadmaps/`):
- `domain/test_roadmap_entities.py` — defaults, enums, to_dict.
- Repo tests (`infrastructure/test_sa_roadmap_repository.py`) against test session:
  create/list/update/delete, cascade delete, by_application, ordering.
- `application/test_roadmap_service.py` — CRUD, validation, progress math, and event
  collection assertions via `InMemoryEventCollector` (rule 16d).
- `presentation/api/test_roadmaps_router.py` — full CRUD via TestClient, 404s, skill
  link resolves by name, progress in detail response.

Run: `uv run pytest apps/backend/tests/ -v`.

## Constraints

- No AI / LLM calls in this prompt (generation is 146).
- Respect AGENTS.md rules: no raw SQL, no cross-context FKs, no `print()` (structlog),
  new-schema-first migrations, newest-first list ordering, per-context router,
  docs-first (events + domain doc committed with the change).
- Roadmap stays independent of the Applications context (logical `application_id` only).
- Do NOT change anything related to `application_preparations` (removed in 146/147).