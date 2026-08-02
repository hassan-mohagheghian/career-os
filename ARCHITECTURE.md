# Architecture Overview

Job Search Intelligence is a **DDD modular monolith** with a hexagonal backend (FastAPI) and a Feature-Sliced frontend (Next.js).

---

## System Diagram

```
┌──────────────────────────────────────────────┐
│              Next.js (App Router)            │
│  ┌────────┐ ┌──────────┐ ┌───────────────┐  │
│  │  Jobs  │ │Companies │ │ Skills/Resume │  │
│  └───┬────┘ └────┬─────┘ └───────┬───────┘  │
│      │           │               │          │
│  FSD: entities / features / widgets / shared │
└──────┼───────────┼───────────────┼──────────┘
       │           │               │
       │       HTTP REST + SSE     │
┌──────┼───────────┼───────────────┼──────────┐
│      ▼           ▼               ▼          │
│        FastAPI (port 5000)                  │
│  ┌───────────────────────────────────────┐  │
│  │ Bounded Contexts                      │  │
│  │ jobs · companies · skills · rules     │  │
│  │ ai · processing · shared              │  │
│  └───────┬───────────────────────┬───────┘  │
│          │                       │          │
│   ┌──────▼──────┐         ┌──────▼──────┐   │
│   │ PostgreSQL   │         │   Redis     │   │
│   │ (SQLAlchemy) │         │  (broker)   │   │
│   └──────────────┘         └──────┬──────┘   │
└───────────────────────────────────┼─────────┘
                                    │
                     ┌──────────────▼──────────────┐
                     │        TaskIQ Worker        │
                     │        (background)         │
                     └──────────────┬──────────────┘
                                    │
                     ┌──────────────▼──────────────┐
                     │       LLMService (AI)       │
                     │      LangGraph workflows    │
                     │  ┌──────┬──────┬────────┐   │
                     │  │OpenAI│ Mimo │ Local  │   │
                     │  └──────┴──────┴────────┘   │
                     └─────────────────────────────┘
```

---

## Architecture Layers

| Layer          | Responsibility                                    |
| -------------- | ------------------------------------------------- |
| Presentation   | FastAPI routers, Pydantic schemas, SSE endpoints  |
| Application    | Use cases, services, commands, DTOs               |
| Domain         | Entities, value objects, repository interfaces, events |
| Infrastructure | SQLAlchemy models/repositories, workers, AI providers, prompts |
| Shared Kernel  | Config, logging (structlog), DI, database          |

---

## Bounded Contexts

| Context    | Purpose                                                        |
| ---------- | -------------------------------------------------------------- |
| jobs       | Job lifecycle: import, process, score, list                    |
| companies  | Company profiles, intelligence, visa assessment                |
| skills     | 5-category taxonomy, aliases, relationships, roadmaps           |
| rules      | Configurable scoring rules (SHARED, JOB, COMPANY_PRODUCT, ...) |
| ai         | LLMService, providers, tools, LangGraph graphs, prompt registry |
| processing | ProcessingExecution, workflow progress, events, queue          |
| shared     | Shared Kernel used by all contexts                              |

Contexts must not cross-import. Dependencies flow domain → application → infrastructure → presentation.

---

## AI Layer

- **LLMService** — single facade for all AI calls; providers are never called directly.
- **Provider abstraction** — swap via `AI_PROVIDER` env var (openai, mimo, local, gemini, ...).
- **LangGraph workflows** — stateful pipelines (JobProcessing, CompanyProcessing, JobContextPreparation).
- **Prompt Platform** — typed, versioned prompts owned by bounded contexts (`ai/infrastructure/prompts/`).

---

## Background Execution

```
API → ProcessingExecution → TaskIQ task → TaskIQ worker → LangGraph workflow → result + events
```

- TaskIQ owns background execution and retries.
- LangGraph owns workflow state and node execution.
- Progress is exposed to the frontend through SSE events.

---

## Realtime (SSE)

- `GET /api/sse/processing-events` streams user-facing execution events.
- Frontend combines a REST snapshot (`/api/processing/queue`) with the SSE stream for live UI.

---

## Data Flow — Job Processing

```
Job URL
  ↓
ProcessingExecution (created)
  ↓
TaskIQ background task
  ↓
LangGraph workflow: load job → collect sources → fetch → extract → build context → validate
  ↓
SSE progress events
  ↓
Save result + scores
```

---

## Design Decisions

- DDD modular monolith + hexagonal architecture (8 contexts)
- SQLAlchemy ORM + Alembic (never raw SQL)
- FastAPI + Pydantic v2 (automatic OpenAPI docs)
- Feature-Sliced frontend (entities / features / widgets / shared)
- Provider abstraction for all AI calls
- LangGraph for multi-step AI pipelines
- TaskIQ + Redis for background processing
- SSE for real-time processing visualization

---

## More Details

- `docs/architecture/ARCHITECTURE.md` — full system design
- `docs/architecture/` — bounded-context analysis, DDD structure, dependency rules
- `docs/ai/` — AI architecture, LangGraph, prompt platform
- `docs/domain/` — domain entities and processing execution
- `docs/queue/` — TaskIQ / ARQ processing
