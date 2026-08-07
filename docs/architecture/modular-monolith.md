# Modular Monolith — DDD Bounded Contexts

## Overview

The backend uses a **modular monolith** architecture with 8 bounded contexts. Each context has `domain/` and `infrastructure/` layers. `shared/` is the shared kernel.

## Actual Structure

```
apps/backend/
├── entrypoints/                   # Application entry points
│   ├── cli.py                     # Typer CLI
│   └── api.py                     # FastAPI app + SocketIO
├── config.py
├── dependencies.py
├── exceptions.py                    # Re-exports from shared.kernel.exceptions
├── cli.py
│
├── shared/                          # SHARED KERNEL
│   ├── domain/
│   │   ├── entity.py               # BaseEntity
│   │   ├── value_object.py         # ValueObject
│   │   ├── domain_event.py         # DomainEvent
│   │   └── repository.py          # RepositoryInterface
│   ├── application/
│   │   ├── exceptions.py           # AppError, NotFoundError, etc.
│   │   └── dto.py                  # BaseDTO, PaginationDTO
│   └── infrastructure/
│       ├── database/
│       │   ├── sqlalchemy_config.py  # Engine, SessionLocal, Base
│       │   ├── session.py           # get_session, get_session_sync
│       │   ├── mappers.py           # model↔dict converters (all contexts)
│       │   └── models/
│       │       └── misc_models.py   # Summary, Resume, Preference, etc.
│       ├── websocket/
│       │   ├── broadcaster.py
│       │   ├── manager.py
│       │   └── session_manager.py
│       └── workers/
│           └── background.py
│
│   └── presentation/
│       ├── api/
│       │   ├── root_router.py      # Central API router (prefix="/api")
│       │   ├── websocket_router.py
│       │   └── sse_router.py
│       ├── cli.py
│       └── error_handler.py
│
├── jobs/                            # JOBS CONTEXT
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── job.py              # Job (aggregate root, PK=id)
│   │   │   ├── summary.py          # Summary entity
│   │   │   ├── job_score.py        # JobScore (value object)
│   │   │   ├── job_location.py     # JobLocation (value object)
│   │   │   └── workflow_log.py     # WorkflowLog (value object)
│   │   └── repositories/
│   │       ├── job_repository.py   # IJobRepository
│   │       └── summary_repository.py
│   └── infrastructure/
│       ├── models/
│       │   ├── job_model.py        # JobModel (SQLAlchemy)
│       │   └── misc_models.py      # SummaryModel
│       └── repositories/
│           ├── sa_job_repository.py
│           └── sa_summary_repository.py
│
├── companies/                       # COMPANIES CONTEXT
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── company.py
│   │   │   ├── company_intelligence.py
│   │   │   └── company_link.py
│   │   └── repositories/
│   │       ├── company_repository.py
│   │       ├── company_intelligence_repository.py
│   │       └── company_link_repository.py
│   └── infrastructure/
│       ├── models/
│       │   └── company_model.py
│       └── repositories/
│           ├── sa_company_repository.py
│           ├── sa_company_intelligence_repository.py
│           └── sa_company_link_repository.py
│
├── skills/                          # SKILLS CONTEXT
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── skill.py
│   │   │   ├── skill_alias.py
│   │   │   └── skill_relationship.py
│   │   └── repositories/
│   │       ├── skill_repository.py
│   │       ├── skill_alias_repository.py
│   │       └── skill_relationship_repository.py
│   └── infrastructure/
│       ├── models/
│       │   └── skill_model.py
│       └── repositories/
│           ├── sa_skill_repository.py
│           ├── sa_skill_alias_repository.py
│           └── sa_skill_relationship_repository.py
│
├── rules/                           # RULES CONTEXT
│   ├── domain/
│   │   ├── entities/
│   │   │   └── rule.py
│   │   └── repositories/
│   │       └── rule_repository.py
│   └── infrastructure/
│       ├── models/
│       └── repositories/
│           └── sa_rule_repository.py
│
│                                        # Resume lives in jobs/ domain + infra
│
├── pending/                         # PENDING QUEUE CONTEXT
│   ├── domain/
│   │   └── repositories/
│   │       ├── pending_repository.py
│   │       └── pending_generation_repository.py
│   └── infrastructure/
│       ├── models/
│       │   ├── pending_model.py
│       │   └── misc_models.py
│       └── repositories/
│           ├── sa_pending_repository.py
│           └── sa_pending_generation_repository.py
│
├── ai/                              # AI CONTEXT (unchanged)
│   ├── service.py
│   ├── providers/
│   ├── agents/
│   └── tools/
│
├── core/                            # LEGACY (still exists)
│   ├── db.py
│   └── queue.py
│
├── services/                        # LEGACY (still exists)
├── schemas/                         # LEGACY (still exists)
├── prompts/
├── scripts/
├── tests/
├── static/
└── logs/
```

## Import Conventions

```python
# Within a context
from jobs.domain.entities.job import Job
from jobs.domain.repositories.job_repository import IJobRepository
from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository

# Cross-context (via shared kernel)
from shared.domain.entity import BaseEntity
from shared.infrastructure.database.session import get_session_sync
from shared.infrastructure.database.mappers import job_model_to_dict
from shared.kernel.exceptions import NotFoundError

# Lazy imports (context __init__.py files use __getattr__ to avoid circular deps)
from jobs.infrastructure import SQLAlchemyJobRepository  # triggers lazy load
from companies.infrastructure import CompanyModel  # triggers lazy load
```

## Alembic

`alembic/env.py` imports from `shared.infrastructure.database.sqlalchemy_config` and `shared.infrastructure.database.models` — both use lazy imports to avoid circular dependencies.

## Test Status

324 tests passing (pre-existing httpx issue excluded from test_api_routes.py).
