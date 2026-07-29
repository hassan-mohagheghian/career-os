# Job Search Intelligence

AI-powered career platform for software engineers — job discovery, company analysis, skill management, resume generation, and career insights. Built for visa-sponsored roles in Europe (Germany, Netherlands).

## Quick Start

```bash
./start
```

Opens FastAPI backend (port 5000) + Next.js frontend (port 5173) + optional background worker (arq + Redis).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14+, FastAPI, SQLite (SQLAlchemy ORM + Alembic), python-socketio |
| Frontend | React 18, Next.js (App Router), TypeScript, shadcn/ui, Tailwind CSS |
| AI | LLMService (OpenAI / Mimo CLI / Local via `AI_PROVIDER`), LangGraph workflows |
| Queue | ARQ + Redis for background job processing |
| Realtime | WebSocket (python-socketio, ASGI mode) |
| Testing | pytest (535+ tests), vitest (401 tests) |
| API Docs | Swagger UI (`/api/docs`), ReDoc (`/api/redoc`) |

## Architecture

```
                     ┌──────────────────────────────┐
                     │    Next.js (App Router)       │
                     │   ┌──────┐ ┌──────────┐      │
                     │   │ Jobs │ │Companies │      │
                     │   ├──────┤ ├──────────┤      │
                     │   │Skills│ │  Resume  │      │
                     │   ├──────┤ ├──────────┤      │
                     │   │Rules │ │  ...     │      │
                     │   └──────┴────────────┘      │
                     │   FSD: entities/features/    │
                     │        widgets/shared         │
                     └──────────────┬───────────────┘
                                    │ HTTP + WebSocket
                     ┌──────────────┼───────────────┐
                     │    FastAPI (port 5000)         │
                     │  ┌──────┐ ┌──────┐ ┌──────┐  │
                     │  │ Jobs │ │Comp. │ │Skills│  │
                     │  ├──────┤ ├──────┤ ├──────┤  │
                     │  │Rules │ │ AI   │ │Shared│  │
                     │  └──┬───┘ └──┬───┘ └──────┘  │
                     │     └────────┴──┐             │
                     │          ┌──────▼──────┐      │
                     │          │  SQLite DB   │      │
                     │          └──────┬──────┘      │
                     └─────────────────┼─────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │    ARQ Worker     │     Redis         │
                    │  (background/)    │  (queue + cache)  │
                    └──────────────────┴──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │       AI Agent Layer (LLMService)    │
                    │    LangGraph workflows + Providers    │
                    │  ┌──────┬──────┬──────┬──────────┐   │
                    │  │OpenAI│ Mimo │Local │ Anthropic│   │
                    │  └──────┴──────┴──────┴──────────┘   │
                    └─────────────────────────────────────┘
```

## Navigation

```
Jobs              Job processing queue + processed cards
Companies         Company intelligence + processing queue
Skills            Skill management, roadmaps, progress tracking
Resume            Resume/cover letter generation
Rules             Scoring rules configuration
```

## Features

### Job Processing
- URL/notes submission → fetch → extract → AI analysis → score → save
- Real-time WebSocket progress (step-by-step updates per 13-node LangGraph)
- Configurable scoring rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING)
- Version tracking for retries, deduplication by base URL

### Company Intelligence
- Multi-source input (notes + links) for profile extraction
- Product vs Recruiting classification, visa friendliness assessment
- Fit/Success/Overall scoring (A++ to D)

### Skills Management
- 5 categories: Technical, Engineering, Professional, Domain, Career
- Skill aliases/merge, drag-and-drop reorganization
- AI-powered roadmap generation with checkable progress tracking

### Resume Generation
- AI-powered resume tailoring and cover letter generation
- Real-time progress with WebSocket updates
- LinkedIn profile integration

## API Documentation

- **Swagger UI**: `http://localhost:5000/api/docs`
- **ReDoc**: `http://localhost:5000/api/redoc`
- **OpenAPI Spec**: `http://localhost:5000/api/openapi.json`

## WebSocket Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `pending:update` | Server→Client | Job step progress |
| `pending:log` | Server→Client | Job processing logs |
| `pending:complete` | Server→Client | Job finished |
| `pending:error` | Server→Client | Job processing error |
| `company:update` | Server→Client | Company processing progress |
| `generation:*` | Server→Client | Resume/cover generation progress |

## Project Structure

```
app/
├── server/                    # Python FastAPI backend (DDD monolith)
│   ├── entrypoints/           # FastAPI app + SocketIO + Typer CLI
│   ├── shared/                # Shared Kernel (domain, infra, config)
│   ├── jobs/                  # Jobs bounded context
│   ├── companies/             # Companies bounded context
│   ├── skills/                # Skills bounded context
│   ├── rules/                 # Rules bounded context
│   ├── ai/                    # AI bounded context (LLM, LangGraph, providers)
│   └── tests/                 # 535+ tests by bounded context
├── background/                # ARQ background worker
├── client/                    # Next.js frontend (FSD architecture)
│   └── src/
│       ├── app/               # App providers, TanStack Query
│       ├── entities/          # Business entities (job, company, skill, etc.)
│       ├── features/          # Feature slices (jobs, companies, skills, etc.)
│       ├── widgets/           # Page adapters, drawers, terminals
│       ├── shared/            # API client, UI kit, hooks, lib
│       └── layout/            # Header, Sidebar
├── alembic/                   # Database migrations
└── start.py                   # Developer CLI (Typer)
docs/                          # Full documentation index
```

## Testing

```bash
# Backend (535+ tests)
./start test backend

# Frontend (401 tests)
./start test frontend

# All
./start test all

# Or directly:
cd app/server && python3 -m pytest tests/ -v
cd app/client && npm run test
```

## Documentation

See `docs/README.md` for the full index. Key files:

| File | Purpose |
|------|---------|
| `docs/DEVELOPMENT.md` | Setup, env vars, debugging |
| `docs/architecture/ARCHITECTURE.md` | System design, DDD contexts |
| `docs/ai/architecture.md` | AI bounded context, providers, graphs |
| `docs/API.md` | REST API + WebSocket reference |
| `docs/websocket-events.md` | Socket.IO event protocol |
| `docs/workflow-progress.md` | 13-node LangGraph pipeline |
| `docs/feature-sliced-design.md` | FSD frontend architecture |
| `docs/nextjs-app-router.md` | Next.js migration guide |
| `docs/tanstack-query.md` | TanStack Query patterns |
| `docs/DOMAIN.md` | Business entities and rules |
| `docs/FEATURES.md` | Feature descriptions and status |
| `docs/development/cli.md` | CLI reference |
