# Agent Instructions

This file gives AI coding agents the context needed to work correctly in this repository.

## Project Overview

**Job Search Intelligence** is an AI-powered career platform for software engineers seeking visa-sponsored roles in Europe (Germany, Netherlands). It automates the job search workflow:

- Job discovery and processing (URL → fetch → extract → AI analysis → score → save)
- Company intelligence (profile extraction, visa assessment, Fit/Success/Overall scoring)
- Skills management (5-category taxonomy, aliases, AI roadmaps)
- Career insights (health score, market analysis, opportunity funnel)
- Resume and cover letter generation

## Quick Start

```bash
./start                                    # backend (5000) + frontend (5173)
uv run uvicorn apps.backend.entrypoints.api:fastapi_app --reload --port 5000
cd apps/frontend && npm run dev               # frontend dev server
```

## Tech Stack

| Layer    | Technology                                                             |
| -------- | ---------------------------------------------------------------------- |
| Backend  | Python 3.14, FastAPI, SQLAlchemy ORM + Alembic, Pydantic v2, structlog |
| Frontend | React, Next.js (App Router), TypeScript, shadcn/ui, Tailwind CSS       |
| AI       | LLMService + provider abstraction, LangGraph workflows                 |
| Queue    | TaskIQ + Redis background workers                                      |
| Realtime | SSE (`/api/sse/processing-events`)                                     |
| Testing  | pytest (backend), vitest (frontend)                                    |

## Repository Layout

```
app/
├── server/                    # Python FastAPI backend (DDD modular monolith)
│   ├── entrypoints/           # FastAPI app + SocketIO + CLI
│   ├── shared/                # Shared Kernel (domain, application, infrastructure)
│   ├── jobs/                  # Jobs bounded context
│   ├── companies/             # Companies bounded context
│   ├── skills/                # Skills bounded context
│   ├── rules/                 # Rules bounded context
│   ├── ai/                    # AI bounded context (LLM, LangGraph, providers)
│   ├── processing/            # Processing bounded context (executions, queue)
│   └── tests/                 # Test suite by bounded context
├── client/                    # Next.js frontend (FSD architecture)
│   └── src/
│       ├── app/               # App providers
│       ├── entities/          # Business entities
│       ├── features/          # Feature slices (jobs, companies, skills, ...)
│       ├── widgets/           # Page adapters, drawers
│       └── shared/            # API client, UI kit, hooks
├── alembic/                   # Database migrations
├── todo-prompts/              # Engineering task prompts for TODO generation (gitignored)
└── docs/                      # Full documentation
```

## Key Rules (Non-Negotiable)

1. All AI calls go through `LLMService` — never call providers directly.
2. Use SQLAlchemy ORM for all database access — never raw SQL.
3. All frontend code is TypeScript (`.ts` / `.tsx`) — no JavaScript.
4. Feature-based frontend: `entities/`, `features/`, `widgets/`, `shared/`.
5. Backend follows DDD modular monolith + hexagonal architecture.
6. Follow DDD / CQRS / OOP / SOLID / TDD / Clean Codes throughout.
7. Default sort is newest first (`created_at desc`).
8. Hard delete for processed jobs: delete the job and related tables.
9. All cards must have a delete button.
10. Do not add API routes in `entrypoints/api.py` — use per-context routers.
11. Do not use `print()` — use `structlog`.

## Testing

```bash
# Backend
uv run pytest apps/backend/tests/ -v

# Frontend
cd apps/frontend && npx vitest run

# All
uv run pytest apps/backend/tests/ -v && cd apps/frontend && npx vitest run
```

## Before Making Changes

1. Read the relevant documentation under `docs/` (context, domain, architecture, API, UX).
2. Understand the affected module and its neighbors.
3. Preserve architecture boundaries (contexts must not cross-import).
4. Implement with minimal, focused changes.
5. Add or update tests for any changed behavior.
6. Verify the relevant test suite passes.

## Documentation Entry Points

| File              | Purpose                                                          |
| ----------------- | ---------------------------------------------------------------- |
| `CONTEXT.md`      | Project context, target users, key rules                         |
| `DOMAIN.md`       | Core entities and business rules                                 |
| `ARCHITECTURE.md` | System design overview                                           |
| `API.md`          | API overview                                                     |
| `DESIGN.md`       | Product & UX design overview + wireframes                        |
| `docs/`           | Full documentation (ai/, api/, architecture/, domain/, ux/, ...) |
