# Prompt 063 - Move Shared Database Infrastructure Into Bounded Contexts

## Objective

Slim `apps/backend/shared/infrastructure/database/` down to only genuine
shared DB infrastructure (`sqlalchemy_config.py`, `session.py`) by moving every
real model, mapper, and repository into its owning bounded context while
preserving each table's PostgreSQL schema. Delete all compatibility shims and
update every production + test import. Split `SQLAlchemyPendingRepository` into
per-context repos and delete the unused `CityModel`.

A database backup is taken before any code change.

---

## Current State

`shared/infrastructure/database/` mixes four kinds of content:

- Genuinely shared infra: `sqlalchemy_config.py` (`Base`, `engine`,
  `SessionLocal`, `SCHEMAS`, `ensure_schemas`), `session.py`
  (`get_session` / `get_session_sync`).
- Real implementations that belong in contexts: `mappers.py`,
  `models/misc_models.py`, `sa_pending_repository.py`,
  `sa_pending_generation_repository.py`.
- Pure re-export shims: `models/{job,company,skill,pending}_model.py` and all
  `sa_*_repository.py` files (delegating to context code).
- Dead duplicates: `jobs/infrastructure/models/misc_models.py` and
  `skills/infrastructure/models/misc_models.py` (un-schema-qualified copies of
  the canonical `misc_models.py`).

The DB schemas (job / company / skill / ai / processing / shared) do NOT
change — only the Python module location of each model class. `__table_args__`
`schema` is preserved verbatim. No Alembic migration is required.

---

# Implementation Steps

## Phase 0 — Pre-flight

1. Backup Postgres `jobsearch` DB (`docker compose exec -T postgres pg_dump -U
   jobsearch -d jobsearch -F c > backups/jobsearch_<ts>.dump`).
2. Create this implementation-history file (committed with the change).

## Phase 1 — Move mappers

Split `database/mappers.py` into:

- `jobs/infrastructure/mappers.py` — `_to_str`, `job_model_to_dict`,
  `dict_to_job_model`, `resume_model_to_dict`.
- `skills/infrastructure/mappers.py` — `_to_str`, `skill_model_to_dict`,
  `dict_to_skill_model`.
- `companies/infrastructure/mappers.py` — `_to_str`, `company_model_to_dict`,
  `dict_to_company_model`, `company_intelligence_model_to_dict`.

`_to_str` is duplicated in each module (trivial datetime normalizer). Update all
importers and the lazy `__init__.py` packages of each context.

## Phase 2 — Move models (preserve schema)

- jobs (schema `job`): rewrite `jobs/infrastructure/models/misc_models.py` to
  contain only schema-qualified `SummaryModel` and `ResumeModel`.
- skills (schema `skill`): new
  `skills/infrastructure/models/skill_roadmap_models.py` with
  `SkillRoadmapModel`, `SkillRoadmapProgressModel`, `SkillRoadmapJobModel`;
  delete the dead `skills/infrastructure/models/misc_models.py`.
- rules (schema `shared`): new `rules/infrastructure/models/rule_model.py`
  with `RuleModel`.
- Delete `CityModel` (unused) and the shared `models/misc_models.py`.
- Update all importers of `shared.infrastructure.database.models.misc_models`.

## Phase 3 — Move repositories

Split `SQLAlchemyPendingRepository` (drop the `table` param):

- `jobs/infrastructure/repositories/sa_pending_job_repository.py` →
  `SQLAlchemyPendingJobRepository` (JobModel branches).
- `companies/infrastructure/repositories/sa_pending_company_repository.py` →
  `SQLAlchemyPendingCompanyRepository` (CompanyModel branches).

Move `sa_pending_generation_repository.py` → `jobs/infrastructure/repositories/`.

Update callers: `shared/presentation/api/root_router.py`,
`shared/infrastructure/stream_server.py`, `shared/presentation/api/websocket_router.py`,
`entrypoints/cli.py`, `shared/infrastructure/repositories/generation_repository.py`,
`companies/presentation/api/pending_router.py`, `dependencies.py`,
`jobs/infrastructure/workers/generation_worker.py`,
`jobs/presentation/api/resumes_router.py`.

## Phase 4 — Clean up shared/database

- Keep only `__init__.py`, `sqlalchemy_config.py`, `session.py`.
- Remove the duplicate `get_session` / `get_session_sync` from
  `sqlalchemy_config.py` (session.py is canonical).
- `apps/alembic/env.py`: replace `from shared.infrastructure.database import
  models` with imports of the context model packages so `Base.metadata`
  discovers every model.
- Delete `mappers.py`, `models/`, all `sa_*` files.

## Phase 5 — Update tests

- Split `tests/shared/infrastructure/database/test_sa_pending_repository_extra.py`
  and `tests/processing/infrastructure/repositories/test_pending_repository.py`
  into job and company test files under the context test dirs.
- Rewrite `TestSAPendingRepository` in `tests/shared/infrastructure/repositories/test_sa_repositories.py`
  against the two new repos; update all model-shim imports.
- Update `tests/conftest.py` and the remaining test files importing shared
  database paths.

---

# Testing Requirements

- `uv run pytest apps/backend/tests/ -v` passes.
- `./scripts/check-version.sh` passes.
- Alembic `env.py` imports succeed and `Base.metadata` model count is unchanged.

---

# Important Constraints

- All AI calls still go through `LLMService`; this is a pure persistence-layer
  relocation.
- No DB schema changes — no new Alembic migration.
- Bounded contexts must not cross-import domain/application layers; repository
  and model imports between contexts are limited to existing patterns.
- Code, tests, and docs must not drift — update docs (API.md if route-visible
  paths change) alongside code.
