# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│              React SPA (Vite + TypeScript)                │
│  ┌──────┐ ┌──────────┐ ┌─────────┐ ┌────────┐ ┌──────┐│
│  │ Jobs │ │Companies │ │Insights │ │ Skills │ │Resume││
│  └──┬───┘ └────┬─────┘ └────┬────┘ └───┬────┘ └──┬───┘│
│     └──────────┴────────────┴──────────┴─────────┘     │
│                  Hash-based routing                      │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────┼───────────────────────────────┐
│               FastAPI (port 5000)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  Routers │ │Services  │ │  Repos   │ │ WebSocket│  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       └────────────┴────────────┴────────────┘         │
│            ┌────────────▼────────────┐                  │
│            │      SQLite DB          │                  │
│            │      (jobs.db)          │                  │
│            └─────────────────────────┘                  │
└─────────────────────────┬───────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │   AI Agent Layer      │
              │   (LLMService)        │
              └───────────┬───────────┘
                          │
              ┌───────────▼───────────┐
              │   Provider Layer      │
              │  ┌─────┬──────┬─────┐│
               │  │Mimo  │OpenAI│Local││
              │  └─────┴──────┴─────┘│
              └───────────────────────┘
```

**Stack**: React 18 + TypeScript + Vite 6 + shadcn/ui + Tailwind CSS | FastAPI + Python 3.14 + SQLite + SQLAlchemy ORM | Pydantic v2 | AI Agent Layer (LLMService + LangGraph) | WebSocket (native FastAPI)

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                     │
│              (FastAPI Routers + WebSocket)                │
│         request validation, response serialization       │
├─────────────────────────────────────────────────────────┤
│                   Application Layer                      │
│            (Services + Use Cases + DTOs)                  │
│         orchestration, business workflow                  │
├─────────────────────────────────────────────────────────┤
│                     Domain Layer                         │
│          (Entities + Value Objects + Events)              │
│         business rules, invariants                        │
├─────────────────────────────────────────────────────────┤
│                 Infrastructure Layer                     │
│        (DB + External APIs + File System)                 │
│         persistence, third-party integration              │
├─────────────────────────────────────────────────────────┤
│                    Shared/Core Layer                      │
│          (Config + Logging + Dependencies)                │
│         cross-cutting concerns                            │
└─────────────────────────────────────────────────────────┘
```

## Core Entities

| Entity                 | Table                    | Purpose                                                                       |
| ---------------------- | ------------------------ | ----------------------------------------------------------------------------- |
| Job                    | `jobs`                   | Processed postings with scores (fit_score, success_score, overall_score)      |
| Job Analysis           | `job_analysis` (schema `job`) | Canonical LLM analysis per job (payload, scores, recommendation, summary, prompt/schema versions) |
| Company                | `companies`              | Profiles with industry, tech_stack, funding_stage                             |
| Company Intelligence   | `company_intelligence`   | AI analysis per company                                                       |
| Resume                 | `resumes`                | Master, tailored, cover letters, LinkedIn                                     |
| Rules                  | `rules`                  | Configurable scoring rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING) |
| Skills                 | `skills`                 | Skills with category, confidence, market_relevance, source                    |
| Skill Aliases          | `skill_aliases`          | Merged skill variants (canonical skill_id → alias_name)                       |
| Skill Relationships    | `skill_relationships`    | Related, similar, parent, child, alternative links                            |
| Skill Roadmaps         | `skill_roadmaps`         | Hierarchical learning trees per skill                                         |
| Skill Roadmap Progress | `skill_roadmap_progress` | User completion tracking                                                      |
| Skill Roadmap Jobs     | `skill_roadmap_jobs`     | Generation job status                                                         |

```
jobs ── company ── company_intelligence
  │                  └── company_links
  ├── resumes
  └── processing_executions (processing queue)

skills ── skill_aliases
  ├── skill_relationships
  ├── skill_roadmaps ── skill_roadmap_progress
  └── skill_roadmap_jobs
```

## Navigation Structure

```
JOBS
  ├── Jobs           Job processing queue + processed cards
  └── Companies      Company intelligence + processing

GROWTH PATH
  └── Skills         Skill management, roadmaps, progress tracking

INSIGHTS
  ├── Overview       Career health score, next actions
  ├── Skills         Skills analysis (extracted skills, fill into DB)
  ├── Opportunities  Job funnel, best jobs, missed opportunities
  ├── Companies      Company scoring, top targets
  ├── Market         Countries, cities, remote opportunities
  └── Networking     Connection strategy, LinkedIn targets

SETTINGS
  ├── Resume         Resume/cover letter generation
  └── Rules          Scoring rules configuration
```

## Backend Structure (DDD Modular Monolith)

```
app/
├── server/
│   ├── entrypoints/           Application entry points
│   │   ├── api.py             FastAPI app factory + SocketIO (ASGI)
│   │   └── cli.py             Typer CLI for job management
│   ├── shared/                Shared Kernel (cross-cutting concerns)
│   │   ├── domain/            Base entity, value objects, repository interfaces
│   │   ├── application/       DTOs, exceptions (AppError hierarchy), schemas
│   │   ├── presentation/      Root API router, WebSocket router, error handlers
│   │   └── infrastructure/    Config, DB (SQLAlchemy), workers, AI compat, logging, websocket
│   ├── jobs/                  Jobs Bounded Context
│   │   ├── domain/            Job entity, value objects (scores, location), repository interfaces
│   │   ├── application/       Use cases, commands (backfill, process, normalize), DTOs
│   │   ├── infrastructure/    SQLAlchemy models + repositories, workers, AI prompts
│   │   └── presentation/      FastAPI routers + Pydantic schemas
│   ├── companies/             Companies Bounded Context
│   │   ├── domain/            Company, CompanyLink, CompanyIntelligence entities
│   │   ├── application/       Use cases
│   │   ├── infrastructure/    SQLAlchemy models, repositories, workers, AI prompts
│   │   └── presentation/      FastAPI routers + schemas
│   ├── skills/                Skills Bounded Context
│   │   ├── domain/            Skill entity, repository interfaces (7 repos)
│   │   ├── application/       Service layer (roadmap generation, OOP wrappers)
│   │   ├── infrastructure/    SQLAlchemy models, repositories, AI prompts
│   │   └── presentation/      FastAPI routers + schemas
│   ├── rules/                 Rules Bounded Context (Scoring Rules)
│   │   ├── domain/            Rule entity, repository interfaces
│   │   ├── infrastructure/    SQLAlchemy repositories
│   │   └── presentation/      FastAPI routers + schemas
│   │                             Resume lives in jobs/ context:
│   │                             jobs/domain/entities/resume.py
│   │                             jobs/infrastructure/repositories/sa_resume_repository.py
│   │                             jobs/presentation/api/resumes_router.py
│   ├── ai/                    AI Bounded Context
│   │   ├── domain/            Generation session entities, value objects
│   │   ├── application/       Use cases, commands, DTOs
│   │   └── infrastructure/    Providers, tools, graphs, prompts
│   │       ├── providers/     LLM provider implementations (mimo, openai, local, gemini, ...)
│   │       ├── tools/         Domain tools (fetch, web, database, job, company, skill, resume)
│   │       ├── graphs/        LangGraph workflows (JobProcessing, CompanyProcessing, etc.)
│   │       └── prompts/       Centralized PromptRegistry (10+ registered prompts)
│   ├── dependencies.py        FastAPI dependency injection
│   ├── exceptions.py          Re-exports from shared.application.exceptions
│   └── tests/                 Test suite by bounded context (376+ tests)
│       ├── ai/                ~70 AI layer tests
│       ├── jobs/
│       ├── companies/
│       ├── skills/
│       ├── rules/
│       ├── processing/
│       ├── shared/
│       └── migration/
└── client/
    └── src/
        ├── features/       Feature-based (each has components/, hooks/)
        ├── shared/         Shared UI, hooks, lib
        └── layout/         Header, Sidebar
```

## AI Agent Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Application Services                    │
│                 (processing runner)                      │
└─────────────────────────┬───────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │      LLMService       │
              │   (Unified Entry)     │
              └───────────┬───────────┘
                          │
              ┌───────────▼───────────┐
              │     LLMProvider       │
              │   (ABC Interface)     │
              └───────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐     ┌──────▼──────┐   ┌─────▼─────┐
    │  Mimo   │     │   OpenAI    │   │   Local   │
    │Provider │     │  Provider   │   │  Provider │
    │(CLI)    │     │             │   │           │
   └─────────┘     └─────────────┘   └───────────┘
```

**Key patterns:**

- **Provider Abstraction**: Swap LLM providers by changing `AI_PROVIDER` env var
- **LLMService**: Single entry point for all AI calls (Facade Pattern)
- **Agent Layer**: Thin orchestration over existing services
- **Tool System**: Domain services wrapping existing business logic
- **Workflow Graphs**: LangGraph-based composable pipelines

## Data Flows

### Job Processing

Two-phase LangGraph pipeline inside a single ProcessingExecution
(`POST /api/jobs/{id}/process` → TaskIQ → `ProcessingExecutionRunner`):

```
Phase 1 — JobContextPreparationGraph (no LLM):
  URL/Notes/Links → load_job → collect_sources → fetch_sources
  → extract_content → build_context → validate_context → persist_context
  → context_ready | execution_failed

Phase 2 — JobAnalysisGraph (exactly one LLM call):
  load_context → prepare_profile → analyze (job.analyze via LLMService)
  → extract_skills → score → recommend → summarize → persist
  → analysis_ready | execution_failed

persist → jobs row projection + summaries (legacy grade) + job_analysis table (schema job)
```

### Company Processing

```
POST /api/companies (queue:true) → ProcessingExecution (COMPANY_PROCESSING)
  Phase 1 (no LLM): load company → collect sources → fetch → extract → build context → validate → persist context
  Phase 2 (one LLM call): load context → prepare profile → analyze → extract → score → persist
→ save to companies + company_intelligence, SSE events with target_type=company
```

### Insights Generation

```
Click Generate → InsightsService → LLMService → per-section prompts (6 sections) → save insights
```

### Skills Intelligence

```
Click Generate → InsightsService → LLMService → skills_intelligence prompt → analyze skills
```

### Skill Roadmap Generation

```
Click Generate → SkillRoadmapService → LLMService → prompts → save to skill_roadmaps + skill_roadmap_progress + emit progress
```

### Resume/Cover Generation

```
Click Generate → GenerationWorker (Template Method) → LLMService → company context enrichment → prompts → save to resumes
```

## Design Decisions

- **DDD Modular Monolith**: 8 bounded contexts with strict dependency rules (domain → application → infrastructure → presentation per context)
- **SQLAlchemy ORM + Alembic**: Clean abstractions with type safety for database access; migrations for schema evolution
- **FastAPI + python-socketio**: Async-native with automatic OpenAPI docs, request validation via Pydantic v2
- **Feature-based frontend**: Each feature owns its components, hooks, and types
- **Concurrency lock**: Only one insights generation at a time
- **Version tracking**: `version` column on processing executions for retry counting
- **Session resumption**: Previous session_id enables continuing interrupted AI sessions
- **Stale run recovery**: On startup, stuck `processing` jobs marked `failed`
- **Font size system**: Custom Tailwind tokens `text-3xs` (6px) and `text-2xs` (8px) for dense dashboard UI
- **API docs**: FastAPI built-in OpenAPI served via Swagger UI (`/api/docs`) and ReDoc (`/api/redoc`)
- **Notes+Links input**: Both jobs and companies accept multi-source input (URL + text notes + labeled links)
- **Provider abstraction**: LLMService wraps all AI calls — never call providers directly
- **LangGraph workflows**: Composable, stateful processing pipelines for multi-step AI operations
- **Template Method pattern**: WorkerBase with Worker subclasses (JobWorker, GenerationWorker)
- **LLMService via Provider abstraction**: Swap providers (Mimo, OpenAI, Local, Gemini, ...) via `AI_PROVIDER` env var
- **DDD/OOP/SOLID/TDD**: Follow domain-driven design, OOP, SOLID principles, and test-driven development

## WebSocket Events

| Event                  | Room              | Purpose                          |
| ---------------------- | ----------------- | -------------------------------- |
| `pending:update`       | `job_{pid}`       | Job step progress                |
| `pending:log`          | `job_{pid}`       | Job processing logs              |
| `pending:complete`     | `job_{pid}`       | Job finished                     |
| `pending:error`        | `job_{pid}`       | Job processing error             |
| `pending:progress`     | `job_{pid}`       | Job progress percentage          |
| `company:update`       | `company_{pid}`   | Company processing progress      |
| `generation:update`    | `generation_{id}` | Resume/cover generation progress |
| `insights:progress`    | insights          | Insights generation progress     |
| `skill_roadmap:update` | skills            | Per-skill roadmap generation     |
| `queue:status`         | —                 | Queue status changes             |

## API Endpoints

### Jobs

| Endpoint                | Method           | Purpose            |
| ----------------------- | ---------------- | ------------------ |
| `/api/jobs`             | GET              | Paginated job list |
| `/api/jobs/:id`         | GET/PATCH/DELETE | Job CRUD           |
| `/api/jobs/:id/process` | POST             | Process job        |

### Companies

| Endpoint                 | Method     | Purpose                  |
| ------------------------ | ---------- | ------------------------ |
| `/api/companies`         | GET/POST   | Company CRUD; POST creates + queues processing (intake) |
| `/api/companies/:id`     | GET/DELETE | Company details/delete   |
| `/api/companies/:id/reprocess` | POST | Re-queue company processing (returns `{status, execution_id}`) |

### Skills

| Endpoint                          | Method     | Purpose                     |
| --------------------------------- | ---------- | --------------------------- |
| `/api/tech-stack`                 | GET/POST   | Skills CRUD                 |
| `/api/tech-stack/:id`             | PUT/DELETE | Update/delete skill         |
| `/api/tech-stack/:id/hide`        | PATCH      | Soft-delete                 |
| `/api/tech-stack/:id/restore`     | PATCH      | Restore hidden              |
| `/api/tech-stack/:id/rename`      | PATCH      | Rename skill                |
| `/api/tech-stack/merge`           | POST       | Merge skills                |
| `/api/tech-stack/hidden`          | GET        | List hidden skills          |
| `/api/skill-roadmaps`             | GET        | Roadmap tree                |
| `/api/skill-roadmaps/generate`    | POST       | AI roadmap generation       |
| `/api/skill-roadmaps/extend`      | POST       | Extend roadmap              |
| `/api/skill-roadmaps/finegrain`   | POST       | Fine-grain roadmap          |
| `/api/skill-roadmap-progress/:id` | PUT        | Toggle topic completion     |
| `/api/skill-roadmap-progress/all` | GET        | All progress summary        |
| `/api/skill-roadmap-progress`     | GET        | Progress for specific skill |

### Insights

| Endpoint                         | Method | Purpose                 |
| -------------------------------- | ------ | ----------------------- |
| `/api/insights`                  | GET    | All insights            |
| `/api/insights/:section`         | GET    | Section data            |
| `/api/insights/refresh`          | POST   | Generate all sections   |
| `/api/insights/:section/refresh` | POST   | Generate single section |
| `/api/insights/progress`         | GET    | Real-time progress      |
| `/api/insights/status`           | GET    | Section statuses        |
| `/api/insights/skills-intel`     | GET    | Skills intelligence     |
| `/api/insights/cancel`           | POST   | Cancel generation       |

### System

| Endpoint                  | Method   | Purpose                                                          |
| ------------------------- | -------- | ---------------------------------------------------------------- |
| `/api/rules`              | GET/PUT  | Scoring rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING) |
| `/api/generation-history` | GET      | Unified generation history (5 source tables)                     |
| `/api/health`             | GET      | Health check                                                     |
| `/api/docs`               | GET      | Swagger UI                                                       |
| `/api/redoc`              | GET      | ReDoc                                                            |
| `/api/openapi.json`       | GET      | OpenAPI 3.0 spec                                                 |
