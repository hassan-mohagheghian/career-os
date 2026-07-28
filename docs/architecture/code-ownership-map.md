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
| `infrastructure/workers/` | `company_worker.py` | Company processing worker |
| `infrastructure/ai/prompts/` | `company/*.txt` | AI prompts for company analysis |
| `presentation/api/` | `companies_router.py` | FastAPI router |
| `presentation/api/schemas/` | `companies.py` | Pydantic schemas |

### Skills Context (`skills/`)

| Layer | Files | Responsibility |
|-------|-------|---------------|
| `domain/entities/` | `skill.py` | Skill domain entity |
| `domain/repositories/` | `skill_repository.py`, `skill_alias_repository.py`, `skill_relationship_repository.py`, `skill_roadmap_repository.py`, `skill_roadmap_progress_repository.py`, `skill_roadmap_job_repository.py`, `tech_learning_repository.py` | Repository interfaces |
| `application/services/` | `skill_roadmap_service.py` | Roadmap generation service |
| `infrastructure/models/` | `skill_model.py`, `misc_models.py` | SQLAlchemy models |
| `infrastructure/repositories/` | `sa_skill_repository.py`, `sa_skill_alias_repository.py`, etc. | Repository implementations |
| `infrastructure/ai/prompts/` | `skill_roadmaps/*.txt` | AI prompts for roadmaps |
| `presentation/api/` | `skills_router.py`, `skill_roadmaps_router.py` | FastAPI routers |
| `presentation/api/schemas/` | `skills.py`, `skill_roadmaps.py` | Pydantic schemas |

### Career Context (`career/`)

| Layer | Files | Responsibility |
|-------|-------|---------------|
| `domain/entities/` | `career_insight.py`, `preference.py` | Career insight and preference entities |
| `domain/repositories/` | `insight_repository.py`, `career_insight_repository.py`, `career_insight_run_repository.py`, `preference_repository.py` | Repository interfaces |
| `application/services/` | `insights.py` | Career intelligence generation service |
| `infrastructure/models/` | `insight_model.py`, `misc_models.py` | SQLAlchemy models |
| `infrastructure/repositories/` | `sa_insight_repository.py`, `sa_career_insight_repository.py`, `sa_career_insight_run_repository.py`, `sa_preference_repository.py` | Repository implementations |
| `infrastructure/ai/prompts/` | `insights/*.txt` | AI prompts for insights |
| `presentation/api/` | `insights_router.py`, `rules_router.py`, `dashboard_router.py` | FastAPI routers |
| `presentation/api/schemas/` | `insights.py`, `rules.py`, `dashboard.py` | Pydantic schemas |

### Resume Context (`resume/`)

| Layer | Files | Responsibility |
|-------|-------|---------------|
| `domain/entities/` | `resume.py` | Resume domain entity |
| `domain/repositories/` | `resume_repository.py` | Repository interface |
| `infrastructure/models/` | `misc_models.py` | SQLAlchemy models |
| `infrastructure/repositories/` | `sa_resume_repository.py` | Repository implementation |
| `infrastructure/workers/` | `generation_worker.py` | Resume/cover letter generation worker |
| `infrastructure/ai/prompts/` | `resume/*.txt` | AI prompts for resume generation |
| `presentation/api/` | `resumes_router.py` | FastAPI router |
| `presentation/api/schemas/` | `resumes.py` | Pydantic schemas |

### Pending Context (`pending/`)

| Layer | Files | Responsibility |
|-------|-------|---------------|
| `domain/entities/` | `pending_job.py` | Pending job entity |
| `domain/repositories/` | `pending_repository.py`, `pending_generation_repository.py` | Repository interfaces |
| `infrastructure/models/` | `pending_model.py`, `misc_models.py` | SQLAlchemy models |
| `infrastructure/repositories/` | `sa_pending_repository.py`, `sa_pending_generation_repository.py` | Repository implementations |
| `presentation/api/` | `pending_router.py`, `pending_companies_router.py` | FastAPI routers |
| `presentation/api/schemas/` | `pending.py` | Pydantic schemas |

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
| `api/v1/*.py` | `*/presentation/api/*_router.py` |
| `core/db.py` | `shared/infrastructure/config/db.py` |
| `core/queue.py` | `shared/infrastructure/config/queue.py` |
| `schemas/*.py` | `*/presentation/api/schemas/*.py` |
| `services/worker.py` | `jobs/infrastructure/workers/worker.py` |
| `services/company_worker.py` | `companies/infrastructure/workers/company_worker.py` |
| `services/generation_worker.py` | `resume/infrastructure/workers/generation_worker.py` |
| `services/insights.py` | `career/application/services/insights.py` |
| `services/skill_roadmap_service.py` | `skills/application/services/skill_roadmap_service.py` |
| `services/process_utils.py` | `shared/infrastructure/process_utils.py` |
| `services/process/*.py` | `shared/infrastructure/process/*.py` |
| `scripts/*.py` | `jobs/application/commands/*.py` |
| `config.py` | `shared/infrastructure/config/app_config.py` |
