# Code Ownership Map

## Bounded Contexts

Each bounded context owns its complete vertical slice: domain, application, infrastructure, and presentation layers.

### Jobs Context (`jobs/`)

| Layer | Files | Responsibility |
|-------|-------|---------------|
| `domain/entities/` | `job.py`, `summary.py` | Job and summary domain entities |
| `domain/value_objects/` | `job_score.py`, `job_location.py`, `workflow_log.py` | Score, location, workflow value objects |
| `domain/repositories/` | `job_repository.py`, `summary_repository.py` | Repository interfaces |
| `application/use_cases/` | `list_jobs.py` | Job listing use case |
| `application/commands/` | `analyze_jobs.py`, `backfill_raw.py`, `backfill_structured.py`, `normalize_locations.py`, `process_pending.py` | CLI commands and batch operations |
| `infrastructure/models/` | `job_model.py`, `misc_models.py` | SQLAlchemy models |
| `infrastructure/repositories/` | `sa_job_repository.py`, `sa_summary_repository.py` | Repository implementations |
| `infrastructure/workers/` | `worker.py` | Job processing worker |
| `infrastructure/ai/prompts/` | `job_processing/*.txt` | AI prompts for job processing |
| `presentation/api/` | `jobs_router.py` | FastAPI router |
| `presentation/api/schemas/` | `jobs.py` | Pydantic schemas |

### Companies Context (`companies/`)

| Layer | Files | Responsibility |
|-------|-------|---------------|
| `domain/entities/` | `company.py`, `company_link.py`, `company_intelligence.py` | Company domain entities |
| `domain/repositories/` | `company_repository.py`, `company_link_repository.py`, `company_intelligence_repository.py` | Repository interfaces |
| `infrastructure/models/` | `company_model.py` | SQLAlchemy models |
| `infrastructure/repositories/` | `sa_company_repository.py`, `sa_company_link_repository.py`, `sa_company_intelligence_repository.py` | Repository implementations |
| `infrastructure/ai/prompts/` | `company/*.txt` | AI prompts for company analysis |
| `presentation/api/` | `companies_router.py` | FastAPI router |
| `presentation/api/schemas/` | `companies.py` | Pydantic schemas |

### Skills Context (`skills/`)

| Layer | Files | Responsibility |
|-------|-------|---------------|
| `domain/entities/` | `skill.py` | Skill domain entity |
| `domain/repositories/` | `skill_repository.py`, `skill_alias_repository.py`, `skill_relationship_repository.py` | Repository interfaces |
| `infrastructure/models/` | `skill_model.py` | SQLAlchemy models |
| `infrastructure/repositories/` | `sa_skill_repository.py`, `sa_skill_alias_repository.py`, `sa_skill_relationship_repository.py` | Repository implementations |
| `presentation/api/` | `skills_router.py` | FastAPI routers |
| `presentation/api/schemas/` | `skills.py` | Pydantic schemas |

### Rules Context (`rules/`)

| Layer | Files | Responsibility |
|-------|-------|---------------|
| `domain/entities/` | `rule.py` | Scoring rule entity |
| `domain/repositories/` | `rule_repository.py` | Repository interface |
| `infrastructure/repositories/` | `sa_rule_repository.py` | Repository implementation |
| `presentation/api/` | `rules_router.py` | FastAPI router |
| `presentation/api/schemas/` | `rules.py` | Pydantic schemas |

### Resume (now part of Jobs Context)

| Layer | Files | Responsibility |
|-------|-------|---------------|
| `jobs/domain/entities/` | `resume.py` | Resume domain entity |
| `jobs/domain/repositories/` | `resume_repository.py` | Repository interface |
| `jobs/infrastructure/repositories/` | `sa_resume_repository.py` | Repository implementation |
| `jobs/presentation/api/` | `resumes_router.py` | FastAPI router |
| `jobs/presentation/api/schemas/` | `resumes.py` | Pydantic schemas |

### Processing Context (`processing/`)

| Layer | Files | Responsibility |
|-------|-------|---------------|
| `domain/entities/` | `processing_execution.py` | ProcessingExecution entity (jobs + companies) |
| `presentation/api/` | `executions_router.py`, `process_router.py` | FastAPI routers (`/processing`, `/jobs`) |

### Shared Kernel (`shared/`)

| Layer | Files | Responsibility |
|-------|-------|---------------|
| `domain/` | `entity.py`, `value_object.py`, `repository.py`, `domain_event.py` | Base domain classes |
| `application/` | `dto.py`, `exceptions.py` | Base DTOs and exceptions |
| `application/schemas/` | `common.py` | Shared Pydantic schemas |
| `infrastructure/database/` | `session.py`, `sqlalchemy_config.py`, `mappers.py`, `models/misc_models.py` | Database configuration |
| `infrastructure/config/` | `app_config.py`, `db.py`, `queue.py` | Application configuration and queue |
| `infrastructure/process/` | `process_manager.py`, `temp_manager.py`, `mimo_runner.py`, `broadcaster.py`, etc. | Process management infrastructure |
| `infrastructure/websocket/` | `manager.py`, `broadcaster.py` | WebSocket infrastructure |
| `infrastructure/workers/` | `background.py` | Background worker utilities |
| `infrastructure/ai/` | `compat.py`, `prompts/` | AI provider abstraction |
| `infrastructure/commands/` | `trigger_processor.py` | Shared CLI commands |
| `infrastructure/utils.py` | | Shared utility functions |
| `presentation/api/` | `websocket_router.py`, `sse_router.py` | Cross-cutting API routers |
| `presentation/cli.py` | | CLI entry point |
| `presentation/error_handler.py` | | Global error handler |

## Legacy Modules (Re-export Shims)

These modules exist at their old locations for backward compatibility. All new code should import from the bounded contexts above.

| Old Location | Re-exports To |
|-------------|---------------|
| `core/db.py` | `shared/infrastructure/config/db.py` |
| `core/queue.py` | `shared/infrastructure/config/queue.py` |
| `schemas/*.py` | `*/presentation/api/schemas/*.py` |
| `services/worker.py` | `jobs/infrastructure/workers/worker.py` |
| `services/generation_worker.py` | `jobs/infrastructure/workers/generation_worker.py` |
| `services/insights.py` | `rules/application/services/insights.py` |
| `services/process_utils.py` | `shared/infrastructure/process_utils.py` |
| `services/process/*.py` | `shared/infrastructure/process/*.py` |
| `scripts/*.py` | `jobs/application/commands/*.py` |
| `config.py` | `shared/infrastructure/config/app_config.py` |
