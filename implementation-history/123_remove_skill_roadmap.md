# Prompt 123 - Remove Skill Roadmap Feature Completely

## Objective

Remove the entire skill "roadmap" feature from both backend and frontend. The
user no longer needs roadmap generation (generate/extend/finegrain) nor the
roadmap tree UI in the skill detail drawer.

Scope of removal:
- Backend skills context: roadmap services, domain repositories, ORM models,
  SQLAlchemy repositories, schemas, router, AI prompts, LangGraph roadmap graph.
- Shared generation history: roadmap enum sources, step configs, generation
  history repository roadmap queries, generation history UI source config.
- Frontend: Roadmap tab in the skill detail drawer, roadmap progress card,
  roadmap source/filter entries, roadmap step configs, merge dialog copy.
- CLI: `--reset-roadmaps` cleanup option.
- Database: drop `skill_roadmaps`, `skill_roadmap_progress`,
  `skill_roadmap_jobs` tables (skill schema) via a new Alembic migration.
- Docs: root guides, docs/api, docs/ai, docs/ux, DESIGN.md, README, scripts.

---

# Current State

The roadmap feature is spread across:

**Backend (skills context)**
- `skills/application/services/skill_roadmap_service.py` — generation logic
- `skills/application/services/skill_roadmap_oop.py` — OOP wrapper
- `skills/domain/repositories/skill_roadmap_{repository,progress_repository,job_repository}.py`
- `skills/infrastructure/models/skill_roadmap_models.py` — 3 tables
- `skills/infrastructure/repositories/sa_skill_roadmap_*.py`
- `skills/presentation/api/skill_roadmaps_router.py` — `/api/skill-roadmaps*`
- `skills/presentation/api/schemas/skill_roadmaps.py`
- `skills/infrastructure/ai/prompts/skill_roadmaps*.txt` (8 prompt files)
- `skills/infrastructure/__init__.py` exports roadmap models/repos

**Backend (shared + wiring)**
- `dependencies.py` — 3 roadmap repo dependencies
- `shared/presentation/api/root_router.py` — router include + compat routes
- `shared/domain/models/generation_models.py` — 3 enum sources + step configs
- `shared/infrastructure/repositories/generation_repository.py` — roadmap queries
- `shared/presentation/api/dashboard_router.py` — skill local-history context
- `shared/infrastructure/database/sqlalchemy_config.py` — skill schema tables
- `shared/infrastructure/config/db.py` + `apps/alembic/env.py` — model imports
- `entrypoints/cli.py` — `--reset-roadmaps`
- `skills/presentation/api/schemas/skills.py` — `total_roadmaps` stat field
- `skills/infrastructure/repositories/sa_skill_repository.py` — rename/merge/stats
- `ai/infrastructure/graphs/skills/roadmap.py` + runtime state/output + registry

**Frontend**
- `skills-v2/components/SkillDetailDrawer.tsx` — Roadmap tab, node tree, actions
- `shared/components/GenerationProgressCard.tsx` — roadmap step config
- `shared/components/GenerationHistoryDrawer.tsx` — roadmap filter option
- `shared/lib/sourceConfig.ts` — roadmap source config
- `features/skills-v2/components/MergeSkillDialog.tsx` — copy mentions roadmaps

---

# Implementation Steps

## 1. Delete backend roadmap files

Delete (via `git rm`):
- `apps/backend/skills/application/services/skill_roadmap_service.py`
- `apps/backend/skills/application/services/skill_roadmap_oop.py`
- `apps/backend/skills/domain/repositories/skill_roadmap_repository.py`
- `apps/backend/skills/domain/repositories/skill_roadmap_progress_repository.py`
- `apps/backend/skills/domain/repositories/skill_roadmap_job_repository.py`
- `apps/backend/skills/infrastructure/models/skill_roadmap_models.py`
- `apps/backend/skills/infrastructure/repositories/sa_skill_roadmap_repository.py`
- `apps/backend/skills/infrastructure/repositories/sa_skill_roadmap_progress_repository.py`
- `apps/backend/skills/infrastructure/repositories/sa_skill_roadmap_job_repository.py`
- `apps/backend/skills/presentation/api/skill_roadmaps_router.py`
- `apps/backend/skills/presentation/api/schemas/skill_roadmaps.py`
- `apps/backend/ai/infrastructure/graphs/skills/roadmap.py`
- prompt files under `skills/infrastructure/ai/prompts/` matching `skill_roadmaps*`

## 2. Update backend wiring

- `dependencies.py`: remove the 3 roadmap dependency functions.
- `root_router.py`: remove roadmap router import/include, the
  `/api/skill-roadmap-progress*`, `/api/skill-roadmap-jobs` compat routes and
  the roadmap DI imports.
- `generation_models.py`: remove the 3 `SKILL_ROADMAP_*` enum values, their
  `group`/`display_name` handling, the 3 `SOURCE_STEP_CONFIG` entries, and the
  roadmap branch in `to_history_item`.
- `generation_repository.py`: remove roadmap imports, `_query_roadmap_jobs`,
  `_query_roadmap_jobs_for_skill`, the roadmap branch in `get_all`, the
  `get_for_skill` method (skill history), and the `skill` branch in
  `get_active_count`. Remove now-unused imports.
- `dashboard_router.py`: remove the `skill` branch from `get_local_history` and
  `get_local_active_count` (the `context == 'skill'` handling), or remove
  `skill_name` param usage accordingly.
- `cli.py`: remove `--reset-roadmaps` option, the `all` mapping, and its block.
- `sqlalchemy_config.py`: drop the 3 roadmap tables from the `skill` SCHEMAS list.
- `config/db.py` + `apps/alembic/env.py`: remove `skill_roadmap_models` import.
- `skills/infrastructure/__init__.py`: remove roadmap exports + `__all__` entries.
- `ai/infrastructure/graphs/skills/__init__.py`: remove roadmap import/export.
- `ai/infrastructure/graphs/__init__.py`: remove `SkillRoadmapState` /
  `SkillRoadmapOutput` imports, the `skill_roadmap` graph entry in
  `get_all_graphs`, docstring line, `__all__` entries.
- `ai/infrastructure/graphs/runtime/state.py`: remove `SkillRoadmapState` and
  `SkillRoadmapOutput`.
- `ai/infrastructure/graphs/runtime/__init__.py`: remove `SkillRoadmapOutput`.
- `ai/infrastructure/parsers.py`: remove `RoadmapGenerationOutput`.
- `shared/infrastructure/process/__init__.py`: remove roadmap service line.
- `skills/presentation/api/schemas/skills.py`: remove `total_roadmaps` field.
- `sa_skill_repository.py`: remove roadmap rename/merge reference updates and
  `total_roadmaps` from `get_stats`.

## 3. Update backend tests

- `tests/conftest.py` and `tests/jobs/presentation/api/conftest.py`: remove
  roadmap dependency imports/overrides.
- `tests/entrypoints/test_cli.py`: remove `test_reset_roadmaps`.
- `tests/shared/presentation/api/test_root_router_compat.py`: remove roadmap
  progress/jobs compat tests and the `_seed_roadmap` helper + model imports.
- `tests/shared/infrastructure/repositories/test_generation_repository.py` and
  `test_generation_repository_extra.py`: remove roadmap job tests.
- `tests/skills/infrastructure/test_skill_management.py`: remove roadmap parts
  of rename/merge tests.
- `tests/shared/infrastructure/config/test_main_config_websocket.py`: remove
  roadmap reference tests and roadmap repo tests.
- `tests/shared/infrastructure/repositories/test_sa_repositories.py`: remove
  the `skill_roadmap_models` import.

## 4. Database migration

After removing the ORM models, generate an Alembic migration scoped to the
skill schema with autogenerate (`ALEMBIC_TARGET_SCHEMA=skill`), then tune its
content to `DROP TABLE` the three roadmap tables in the right dependency order
(`skill_roadmap_jobs`, `skill_roadmap_progress`, `skill_roadmaps`). Downgrade
recreates them. Verify with `alembic history`, `alembic heads`, upgrade and
downgrade/upgrade round-trip per the alembic guide.

Note: because the `skill` schema migration line lives under
`apps/alembic/skill/versions/`, scope autogenerate with `ALEMBIC_TARGET_SCHEMA=skill`
and commit the tuned file with the change.

## 5. Frontend

- `SkillDetailDrawer.tsx`: remove the `RoadmapNode` component, roadmap state,
  `fetchRoadmap` / `runRoadmapAction`, the Roadmap tab trigger + content, the
  "Generate Roadmap" button in Details, and now-unused imports
  (`Plus`, `ArrowsClockwise`, `CaretDown`, `CaretRight`, `Check`, `TreeStructure`).
  Remove `GenerationProgressCard` usage (or keep only if history still uses it).
- `GenerationProgressCard.tsx`: remove the `roadmap` step config; make
  `DEFAULT_STEPS` fall back to the job-processing config or a default.
- `GenerationHistoryDrawer.tsx`: remove the roadmap filter option.
- `sourceConfig.ts`: remove the roadmap source entry + `TreeStructure` import,
  and drop `'roadmap'` from the `source` union type.
- `sourceConfig.test.ts`: remove the roadmap test case.
- `GenerationHistoryDrawer.test.tsx`: remove the roadmap mock item.
- `MergeSkillDialog.tsx`: update copy to "Mentions are re-pointed".

Follow-up (same change): with the roadmap gone, the skill detail drawer has no
usable tabs, so remove the tab bar entirely — the drawer renders the skill
details directly. Remove `Tabs`/`TabsList`/`TabsTrigger`, the `activeTab` state,
the History tab + `useLocalHistory`/`GenerationHistoryItem` usage, and the
now-unused `onRefresh` prop (drop it from the drawer interface and the
`SkillsPage` call site).

## 6. Docs

Update/trim roadmap references in: `AGENTS.md`, `API.md`, `DOMAIN.md`,
`CONTEXT.md`, `ARCHITECTURE.md`, `DESIGN.md`, `README.md`,
`docs/api/api-design.md`, `docs/api/skills/list-skills.md`,
`docs/api/skills/merge-skills.md`, `docs/ai/graphs.md`,
`docs/ai/prompt-registry.md`, `docs/ai/state-management.md`,
`docs/ux/features/skills/*`, `docs/ux/flows/skills/*`, `docs/ux/README.md`,
and the migration scripts (`scripts/migrate_*.py`, `scripts/restore_from_sqlite.py`).

Update the skills UX wireframe docs (`docs/ux/features/skills/skill-detail.md`,
`docs/ux/features/skills/page.md`, `docs/ux/flows/skills/*`) to drop the
Roadmap tab and note the feature was removed. Update `DESIGN.md` wireframes and
`docs/ux/README.md` index.

---

# Testing Requirements

Backend:
- `uv run pytest apps/backend/tests/ -v`
- `uv run alembic history` + `uv run alembic heads` (single head) +
  upgrade/downgrade round-trip.

Frontend:
- `cd apps/frontend && npx vitest run`
- `npm run lint` and `npm run typecheck`

---

# Important Constraints

- No cross-context FKs are touched; only roadmap tables are dropped.
- Do not leave any `roadmap` references that break imports — the whole feature
  (UI + backend + generation history) is removed, not just the UI.
- Follow AGENTS.md rules: use per-context routers (removal, not new routes),
  no `print()`, keep version files in sync only if a release is requested.
