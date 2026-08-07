# Backend Structure

## Folder Structure

```
app/
├── server/                        # FastAPI application root
│   ├── __init__.py
│   ├── entrypoints/               # Application entry points (CLI + API)
│   │   ├── __init__.py
│   │   ├── cli.py                 # Typer CLI for job management
│   │   └── api.py                 # FastAPI app factory, SocketIO, lifespan
│   ├── config.py                  # Settings (pydantic-settings)
│   ├── database.py                # DB connection management
│   ├── dependencies.py            # FastAPI Depends() functions
│   ├── exceptions.py              # Custom exception classes
│   ├── middleware.py              # Request logging, CORS, error handling
│   │
│   ├── jobs/                      # Jobs Bounded Context
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── presentation/api/
│   │       └── jobs_router.py
│   │
│   ├── companies/                 # Companies Bounded Context
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── presentation/api/
│   │       └── companies_router.py
│   │
│   ├── skills/                    # Skills Bounded Context
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── presentation/api/
│   │       └── skills_router.py
│   │
│   ├── rules/                     # Rules (Scoring) Bounded Context
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── presentation/api/
│   │       └── rules_router.py
│   │
│   │                                 # Resume lives in jobs/presentation/api/resumes_router.py
│   │
│   ├── processing/                # Processing Bounded Context (executions + queue)
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   └── presentation/api/
│   │       ├── executions_router.py   # prefix /processing (queue, executions)
│   │       └── process_router.py      # prefix /jobs (job process trigger)
│   │
│   ├── ai/                        # AI Agent Layer
│   │   ├── service.py
│   │   ├── providers/
│   │   ├── agents/
│   │   └── tools/
│   │
│   └── shared/                    # Shared Kernel
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       └── presentation/api/
│           ├── root_router.py     # Central API router (prefix="/api")
│           ├── websocket_router.py
│           └── sse_router.py
│   │
│   ├── domain/                    # Domain Layer
│   │   ├── __init__.py
│   │   ├── entities/             # Domain entities
│   │   │   ├── __init__.py
│   │   │   ├── job.py            # Job entity
│   │   │   ├── company.py        # Company entity
│   │   │   ├── skill.py          # Skill entity
│   │   │   ├── resume.py         # Resume entity
│   │   │   ├── insight.py        # Career insight entity
│   │   │   └── pending.py        # Pending item entity
│   │   ├── value_objects/        # Value objects
│   │   │   ├── __init__.py
│   │   │   ├── score.py          # Score (fit, success, overall)
│   │   │   ├── status.py         # ItemStatus enum
│   │   │   ├── pipeline_step.py  # PipelineStep enum
│   │   │   └── metadata.py       # Timestamps, versions
│   │   ├── events/               # Domain events
│   │   │   ├── __init__.py
│   │   │   ├── processing.py     # ProcessingComplete, ProcessingError
│   │   │   ├── status.py         # StatusUpdate
│   │   │   └── log.py            # LogEntry
│   │   └── repositories/         # Repository interfaces (ABCs)
│   │       ├── __init__.py
│   │       ├── job_repository.py
│   │       ├── company_repository.py
│   │       ├── skill_repository.py
│   │       ├── pending_repository.py
│   │       └── insight_repository.py
│   │
│   ├── application/               # Application Layer
│   │   ├── __init__.py
│   │   ├── services/             # Service classes
│   │   │   ├── __init__.py
│   │   │   ├── job_service.py    # Job business logic
│   │   │   ├── company_service.py # Company business logic
│   │   │   ├── skill_service.py  # Skill business logic
│   │   │   ├── insight_service.py # Career insight logic
│   │   │   ├── resume_service.py # Resume generation logic
│   │   │   ├── pending_service.py # Queue management logic
│   │   │   └── rule_service.py   # Scoring rules logic
│   │   ├── use_cases/            # Complex use cases
│   │   │   ├── __init__.py
│   │   │   ├── process_job.py    # Job processing pipeline
│   │   │   ├── process_company.py # Company processing pipeline
│   │   │   ├── generate_insights.py # Insights generation
│   │   │   └── generate_resume.py # Resume generation
│   │   └── dto/                  # Data Transfer Objects
│   │       ├── __init__.py
│   │       ├── job_dto.py
│   │       ├── company_dto.py
│   │       ├── skill_dto.py
│   │       └── insight_dto.py
│   │
│   ├── infrastructure/            # Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── database/             # Database implementations
│   │   │   ├── __init__.py
│   │   │   ├── connection.py     # SQLite connection management
│   │   │   ├── migrations.py     # Schema migrations
│   │   │   ├── job_repository.py # JobRepository implementation
│   │   │   ├── company_repository.py
│   │   │   ├── skill_repository.py
│   │   │   ├── pending_repository.py
│   │   │   └── insight_repository.py
│   │   ├── ai/                   # AI provider adapters
│   │   │   ├── __init__.py
│   │   │   ├── llm_service.py    # LLMService wrapper
│   │   │   └── providers/        # Provider implementations
│   │   │       ├── __init__.py
│   │   │       ├── base.py       # Provider ABC
│   │   │       ├── mimo.py       # Mimo CLI provider
│   │   │       ├── openai.py     # OpenAI provider
│   │   │       └── local.py      # Local LLM provider
│   │   ├── websocket/            # WebSocket infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── manager.py        # ConnectionManager
│   │   │   └── broadcaster.py    # Event broadcaster
│   │   ├── workers/              # Background workers
│   │   │   ├── __init__.py
│   │   │   ├── job_worker.py     # Job processing worker
│   │   │   ├── insight_worker.py # Insights generation worker
│   │   │   └── resume_worker.py  # Resume generation worker
│   │   └── process/              # Process management
│   │       ├── __init__.py
│   │       ├── manager.py        # Subprocess lifecycle
│   │       ├── temp_manager.py   # Temp file management
│   │       └── mimo_runner.py    # Mimo CLI runner
│   │
│   └── shared/                    # Shared/Core Layer
│       ├── __init__.py
│       ├── config.py             # Configuration constants
│       ├── logging.py            # structlog setup
│       ├── types.py              # Common type aliases
│       └── utils.py              # Shared utilities
│
├── ai/                            # AI Agent Layer (unchanged)
│   ├── service.py                # LLMService facade
│   ├── providers/                # LLM providers
│   ├── agents/                   # LangGraph agents
│   ├── tools/                    # LangChain tools
│   ├── prompts/                  # Prompt templates
│   └── logging.py                # AI-specific logging
│
├── client/                        # Frontend (unchanged)
│   └── src/
│       ├── features/
│       ├── shared/
│       └── layout/
│
tests/                             # Test suite
├── unit/                          # Unit tests
│   ├── domain/                   # Domain entity tests
│   ├── application/              # Service tests
│   └── infrastructure/           # Repository tests
├── integration/                   # Integration tests
│   ├── api/                      # API endpoint tests
│   ├── database/                 # Database operation tests
│   └── websocket/                # WebSocket tests
└── conftest.py                    # Shared fixtures
```

## Module Boundaries

### Layer Dependencies

```
Presentation (api/) 
    → Application (application/) 
    → Domain (domain/)
    ← Infrastructure (infrastructure/)
```

**Rules:**
- Presentation depends on Application and Domain
- Application depends on Domain only
- Infrastructure implements Domain interfaces
- Domain has zero external dependencies

### Import Rules

```python
# ALLOWED: Router imports service
from apps.backend.application.services.job_service import JobService

# ALLOWED: Service imports repository interface
from apps.backend.domain.repositories.job_repository import IJobRepository

# ALLOWED: Infrastructure implements interface
from apps.backend.infrastructure.database.job_repository import JobRepository

# FORBIDDEN: Domain imports infrastructure
from apps.backend.infrastructure.database.connection import get_db  # NO

# FORBIDDEN: Router imports repository directly
from apps.backend.infrastructure.database.job_repository import JobRepository  # NO
```

## Feature Organization

Each bounded context follows this structure:

```
jobs/                              # Jobs Bounded Context
├── domain/
│   ├── entities/job.py            # Entity (domain)
│   └── repositories/job_repository.py  # Interface (domain)
├── application/
│   └── services/job_service.py    # Service (application)
├── infrastructure/
│   ├── models/job_model.py        # SQLAlchemy model
│   └── repositories/sa_job_repository.py  # Implementation (infrastructure)
└── presentation/
    └── api/jobs_router.py         # Router (presentation)
```

### Feature Responsibilities

| Feature | Router | Service | Repository | Events |
|---------|--------|---------|------------|--------|
| Jobs | CRUD, scoring endpoints | Job business logic | Job SQL queries | ProcessingComplete |
| Companies | CRUD, intelligence endpoints | Company business logic | Company SQL queries | CompanyComplete |
| Skills | CRUD, merge, taxonomy | Skill business logic | Skill SQL queries | SkillUpdated |
| Insights | Generation, progress | Insight business logic | Insight SQL queries | InsightsProgress |
| Resumes | Generation endpoints | Resume business logic | Resume SQL queries | GenerationComplete |
| Pending | Queue management | Queue orchestration | Pending SQL queries | StatusUpdate |

## Dependency Injection

### FastAPI Depends() Functions

```python
# dependencies.py
from fastapi import Depends
from apps.backend.infrastructure.database.connection import get_db
from apps.backend.infrastructure.database.job_repository import JobRepository
from apps.backend.application.services.job_service import JobService

async def get_job_repository(db=Depends(get_db)) -> JobRepository:
    return JobRepository(db)

async def get_job_service(repo=Depends(get_job_repository)) -> JobService:
    return JobService(repo)
```

### Router Usage

```python
from fastapi import APIRouter, Depends
from apps.backend.dependencies import get_job_service
from apps.backend.application.services.job_service import JobService

router = APIRouter()

@router.get("/jobs")
async def list_jobs(service: JobService = Depends(get_job_service)):
    return await service.list_jobs()
```

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Router | `plural_noun.py` | `jobs.py`, `companies.py` |
| Service | `singular_noun_service.py` | `job_service.py` |
| Repository | `singular_noun_repository.py` | `job_repository.py` |
| Entity | `singular_noun.py` | `job.py`, `company.py` |
| DTO | `plural_noun_dto.py` | `job_dto.py` |
| Event | `category.py` | `processing.py`, `status.py` |
| Test | `test_<module>.py` | `test_job_service.py` |

## Migration Mapping (Completed)

> The migration from Flask to FastAPI is complete. All old Flask blueprints have been removed. This mapping documents the transition.

### Flask Blueprint → FastAPI Router

| Flask Blueprint | FastAPI Router | Bounded Context |
|-----------------|----------------|-----------------|
| `jobs` | `jobs_router` | `jobs/presentation/api/jobs_router.py` |
| `pending` | `executions_router` | `processing/presentation/api/executions_router.py` |
| `companies` | `companies_router` | `companies/presentation/api/companies_router.py` |
| `resumes` | `resumes_router` | `jobs/presentation/api/resumes_router.py` |
| `skills` | `skills_router` | `skills/presentation/api/skills_router.py` |
| `rules` | `rules_router` | `rules/presentation/api/rules_router.py` |
| `misc` | `dashboard_router` | `shared/presentation/api/dashboard_router.py` |
| `static` | SPA catch-all | `entrypoints/api.py` |
| `api_docs` | Docs endpoints | FastAPI built-in `/docs` |
