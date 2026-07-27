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
              │  │Mimo │OpenAI│Local││
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

| Entity | Table | Purpose |
|--------|-------|---------|
| Job | `jobs` | Processed postings with scores (fit_score, success_score, overall_score) |
| Company | `companies` | Profiles with industry, tech_stack, funding_stage |
| Company Intelligence | `company_intelligence` | AI analysis per company |
| Resume | `resumes` | Master, tailored, cover letters, LinkedIn |
| Preferences | `preferences` | Configurable scoring rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING) |
| Insights | `career_insights` | Versioned intelligence results (overview, opportunities, companies, skills, market, networking) |
| Insight Runs | `career_insight_runs` | Generation workflow tracking |
| Skills | `skills` | Skills with category, confidence, market_relevance, source |
| Skill Aliases | `skill_aliases` | Merged skill variants (canonical skill_id → alias_name) |
| Skill Relationships | `skill_relationships` | Related, similar, parent, child, alternative links |
| Skill Roadmaps | `skill_roadmaps` | Hierarchical learning trees per skill |
| Skill Roadmap Progress | `skill_roadmap_progress` | User completion tracking |
| Skill Roadmap Jobs | `skill_roadmap_jobs` | Generation job status |

```
jobs ── company ── company_intelligence
  │                  └── company_links
  ├── resumes
  └── pending_jobs (processing queue)

career_insight_runs ── career_insights
  └── session tracking

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

## Backend Structure

```
app/
├── ai/                    AI Agent Orchestration Layer
│   ├── service.py         LLMService — unified entry point for all AI calls
│   ├── providers/         LLM provider abstraction (mimo, openai, local)
│   ├── agents/            Agent implementations + LangGraph workflows
│   ├── tools/             Domain tools wrapping existing services
│   ├── prompts/           Centralized prompt registry
│   └── logging.py         Structured agent events
├── server/
│   ├── main.py              FastAPI entry point (primary server)
│   ├── app.py               Flask entry point (legacy, optional)
│   ├── config.py            Centralized path constants + AI_PROVIDER
│   ├── database.py          get_db() helper (Flask compatibility)
│   ├── dependencies.py      FastAPI dependency injection
│   ├── exceptions.py        Custom exception classes
│   ├── migrations.py        Schema + data migrations
│   ├── api/                 FastAPI routers (presentation layer)
│   │   ├── router.py        Root API router
│   │   └── v1/             API v1 endpoints
│   │       ├── jobs.py      Job CRUD, scoring
│   │       ├── companies.py Company CRUD, intelligence
│   │       ├── skills.py    Skills CRUD, merge, taxonomy
│   │       ├── insights.py  Career intelligence endpoints
│   │       ├── pending.py   Processing queue
│   │       ├── resumes.py   Resume/cover letter generation
│   │       ├── skill_roadmaps.py  Roadmap generation
│   │       ├── rules.py     Scoring rules
│   │       ├── dashboard.py Dashboard data, cities
│   │       ├── websocket.py WebSocket endpoint
│   │       └── sse.py       SSE streaming endpoints
│   ├── domain/              Domain layer (interfaces)
│   │   └── repositories/    Repository interfaces (ABCs)
│   ├── infrastructure/      Infrastructure layer (implementations)
│   │   ├── database/        Repository implementations
│   │   ├── websocket/       WebSocket manager + broadcaster
│   │   └── workers/         Background task management
│   ├── schemas/             Pydantic request/response models
│   ├── services/            Business logic services
│   │   ├── worker.py        Job processing pipeline
│   │   ├── company_worker.py Company processing
│   │   ├── insights.py      Career intelligence
│   │   └── process/         Broadcaster, models, process_manager
│   ├── core/                Core infrastructure
│   │   ├── db.py            DB schema, migrations
│   │   └── queue.py         Job queue manager
│   ├── prompts/             AI prompt templates
│   └── tests/               Test suite
└── client/
    └── src/
        ├── features/       Feature-based (each has components/, hooks/)
        ├── shared/         Shared UI, hooks, lib
        └── layout/         Header, Sidebar

tests/test_ai/              70 AI layer tests
```

## AI Agent Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Application Services                    │
│              (worker.py, company_worker.py)              │
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
```
URL/Notes/Links → pending_jobs → worker.py → LLMService → fetch → validate → extract → score → save to jobs
```

### Company Processing
```
Notes/Links → pending_companies → company_worker.py → LLMService → fetch → extract → analyze → save to companies
```

### Insights Generation
```
Click Generate → insights.py → LLMService → per-section prompts → save to career_insights
```

### Skills Intelligence
```
Click Generate → insights.py → LLMService → skills_intelligence prompt → save to career_insights + fill skills
```

### Skill Roadmap Generation
```
Click Generate → skill_roadmaps.py → LLMService → mimo CLI → save to skill_roadmaps + emit progress
```

## Design Decisions

- **SQLAlchemy ORM**: Clean abstractions with type safety for database access
- **Feature-based frontend**: Each feature owns its components, hooks, and types
- **Concurrency lock**: Only one insights generation at a time
- **Version tracking**: `version` column on pending_jobs/companies for retry counting
- **Session resumption**: Previous session_id enables continuing interrupted AI sessions
- **Stale run recovery**: On startup, stuck `processing` jobs marked `failed`
- **Font size system**: Custom Tailwind tokens `text-3xs` (6px) and `text-2xs` (8px) for dense dashboard UI
- **API docs**: Static OpenAPI 3.0 spec served via Swagger UI (`/api/docs/`) and ReDoc (`/api/redoc/`)
- **Notes+Links input**: Both jobs and companies accept multi-source input (URL + text notes + labeled links)
- **Provider abstraction**: LLMService wraps all AI calls — never call MimoRunner directly
- **DDD/SOLID/TDD**: Follow domain-driven design, SOLID principles, and test-driven development
- **Backward compatible**: Existing workers continue to work while using new AI layer

## WebSocket Events

| Event | Room | Purpose |
|-------|------|---------|
| `pending:update` | — | Job step progress |
| `pending:log` | — | Job processing logs |
| `pending:complete` | — | Job finished |
| `company:update` | — | Company processing progress |
| `insights:progress` | insights | Insights generation progress |
| `skill_roadmap:update` | skills | Per-skill roadmap generation |

## API Endpoints

### Jobs
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/jobs` | GET | Paginated job list |
| `/api/jobs/:num` | GET/PUT/DELETE | Job CRUD |
| `/api/jobs/:num/requeue` | POST | Re-queue for processing |
| `/api/jobs/:num/rescore` | POST | Rescore existing job |

### Companies
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/companies` | GET/POST | Company CRUD |
| `/api/companies/:id` | GET/DELETE | Company details/delete |
| `/api/pending-companies` | GET/POST | Company processing queue |

### Skills
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/tech-stack` | GET/POST | Skills CRUD |
| `/api/tech-stack/:id` | PUT/DELETE | Update/delete skill |
| `/api/tech-stack/:id/hide` | PATCH | Soft-delete |
| `/api/tech-stack/:id/restore` | PATCH | Restore hidden |
| `/api/tech-stack/:id/rename` | PATCH | Rename skill |
| `/api/tech-stack/merge` | POST | Merge skills |
| `/api/skill-roadmaps` | GET | Roadmap tree |
| `/api/skill-roadmaps/generate` | POST | AI roadmap generation |
| `/api/skill-roadmaps/extend` | POST | Extend roadmap |
| `/api/skill-roadmaps/finegrain` | POST | Fine-grain roadmap |
| `/api/skill-roadmap-progress/all` | GET | All progress summary |

### Insights
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/insights` | GET | All insights |
| `/api/insights/:section` | GET | Section data |
| `/api/insights/refresh` | POST | Generate all sections |
| `/api/insights/:section/refresh` | POST | Generate single section |
| `/api/insights/progress` | GET | Real-time progress |
| `/api/insights/status` | GET | Section statuses |
| `/api/insights/skills-intel` | GET | Skills intelligence |
| `/api/insights/cancel` | POST | Cancel generation |

### System
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/pending` | GET/POST | Job queue |
| `/api/rules` | GET/PUT | Scoring rules |
| `/api/generation-history` | GET | Unified history |
| `/api/docs/` | GET | Swagger UI |
| `/api/redoc` | GET | ReDoc |
