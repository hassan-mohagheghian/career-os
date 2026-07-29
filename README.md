# Job Search Intelligence

AI-powered career intelligence platform for engineers — job discovery, company analysis, skill management, resume generation, and career insights. Built for visa-sponsored roles in Europe (Germany, Netherlands).

## Quick Start

```bash
./start
```

Opens FastAPI backend (port 5000) + React dev server (port 5173).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14+, FastAPI, SQLite (SQLAlchemy ORM + Alembic), python-socketio |
| Frontend | React 18, TypeScript, Vite 6, shadcn/ui, Tailwind CSS |
| AI | LLMService (Mimo CLI / OpenAI / Local via `AI_PROVIDER`), LangGraph workflows |
| Realtime | WebSocket (python-socketio, ASGI mode) |
| Testing | pytest (376+ tests), vitest (23 tests) |
| API Docs | Swagger UI (`/api/docs`), ReDoc (`/api/redoc`) |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              React SPA (Vite + TypeScript)                │
│  ┌──────┐ ┌──────────┐ ┌─────────┐ ┌────────┐ ┌──────┐│
│  │ Jobs │ │Companies │ │Insights │ │ Skills │ │Resume││
│  └──┬───┘ └────┬─────┘ └────┬────┘ └───┬────┘ └──┬───┘│
│     └──────────┴────────────┴──────────┴─────────┘     │
│                  Hash-based routing                      │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP + WebSocket
┌─────────────────────────┼───────────────────────────────┐
│               FastAPI (port 5000)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  Routers │ │Services  │ │  Repos   │ │ WebSocket│  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       └────────────┴────────────┴────────────┘         │
│            ┌────────────▼────────────┐                   │
│            │      SQLite DB          │                   │
│            │      (jobs.db)          │                   │
│            └─────────────────────────┘                   │
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

## Navigation

```
Jobs              Job processing queue + processed cards
Companies         Company intelligence + processing
Skills            Skill management, roadmaps, progress tracking
Insights          Career intelligence analysis
  ├── Overview    Career health score, next actions
  ├── Skills      Skills analysis (extracted skills, fill into DB)
  ├── Opportunities  Job funnel, best jobs, missed opportunities
  ├── Companies   Company scoring, top targets
  ├── Market      Countries, cities, remote opportunities
  └── Networking  Connection strategy, LinkedIn targets
Settings
  ├── Resume      Resume/cover letter generation
  └── Rules       Scoring rules configuration
```

## Features

### Job Processing
- URL submission → fetch → extract → AI analysis → score → save
- Real-time WebSocket progress (step-by-step updates)
- Configurable scoring rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING)
- Version tracking for retries (version column incremented on reset)

### Company Intelligence
- Company profile extraction and analysis
- Product vs Recruiting classification
- Visa friendliness assessment
- Fit/Success/Overall scoring

### Skills Management
- **5 Categories**: Technical, Engineering, Professional, Domain, Career
- **Skill Aliases**: Merge duplicate skills (e.g., Postgres → PostgreSQL)
- **Drag-and-Drop Merge**: Combine skills across all sections
- **Checkable Roadmaps**: Track learning progress per skill
- **Auto-categorization**: AI categorizes skills from job analysis

### Insights (Career Intelligence)
- Career health score (0-100)
- Strengths, gaps, learning recommendations
- Market analysis (countries, cities, remote)
- Real-time progress with session tracking
- Per-section generation (overview, opportunities, companies, market, networking)

### Resume Generation
- AI-powered resume tailoring
- Cover letter generation
- LinkedIn profile integration

## API Documentation

- **Swagger UI**: `http://localhost:5000/api/docs`
- **ReDoc**: `http://localhost:5000/api/redoc`
- **OpenAPI Spec**: `http://localhost:5000/api/openapi.json`

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/jobs` | GET | Paginated job list |
| `/api/jobs/:num` | GET/PUT/DELETE | Job CRUD |
| `/api/jobs/:num/requeue` | POST | Re-queue for processing |
| `/api/jobs/:num/rescore` | POST | Rescore existing job |
| `/api/pending` | GET/POST | Job queue management |
| `/api/companies` | GET/POST | Company CRUD |
| `/api/companies/:id` | GET/DELETE | Company details/delete |
| `/api/tech-stack` | GET/POST | Skills CRUD |
| `/api/tech-stack/:id/hide` | PATCH | Hide skill |
| `/api/tech-stack/:id/rename` | PATCH | Rename skill |
| `/api/tech-stack/merge` | POST | Merge skills |
| `/api/skill-roadmaps` | GET | Roadmap tree |
| `/api/skill-roadmaps/generate` | POST | AI roadmap generation |
| `/api/insights` | GET | Career insights |
| `/api/insights/:section/refresh` | POST | Generate single section |
| `/api/insights/progress` | GET | Real-time progress |
| `/api/generation-history` | GET | Unified generation history |
| `/api/rules` | GET/PUT | Scoring rules |

## WebSocket Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `pending:update` | Server→Client | Job step progress |
| `pending:log` | Server→Client | Job processing logs |
| `pending:complete` | Server→Client | Job finished |
| `pending:error` | Server→Client | Job processing error |
| `company:update` | Server→Client | Company processing progress |
| `insights:progress` | Server→Client | Insights analysis progress |
| `skill_roadmap:update` | Server→Client | Roadmap generation status |
| `generation:*` | Server→Client | Resume/cover generation progress |

## Project Structure

```
app/
├── server/
│   ├── entrypoints/
│   │   ├── api.py                # FastAPI app factory + SocketIO
│   │   └── cli.py                # Typer CLI for job management
│   ├── shared/                   # Shared Kernel (cross-cutting)
│   │   ├── domain/               # Base entity, value objects, repositories
│   │   ├── application/          # DTOs, exceptions, schemas
│   │   ├── presentation/         # Routers, error handlers, WebSocket
│   │   └── infrastructure/       # Config, DB, workers, AI compat, logging
│   ├── jobs/                     # Jobs Bounded Context
│   │   ├── domain/               # Job entity, value objects, repository interfaces
│   │   ├── application/          # Use cases, commands, DTOs
│   │   ├── infrastructure/       # Models, repositories, workers, AI prompts
│   │   └── presentation/         # FastAPI routers, schemas
│   ├── companies/                # Companies Bounded Context
│   ├── skills/                   # Skills Bounded Context
│   ├── career/                   # Career Bounded Context
│   ├── resume/                   # Resume Bounded Context
│   ├── ai/                       # AI Bounded Context
│   │   ├── domain/               # Generation session entities
│   │   ├── application/          # Use cases, commands, DTOs
│   │   ├── infrastructure/       # Providers (Mimo/OpenAI/Local/Gemini), tools, graphs
│   │   │   ├── providers/        # LLM provider implementations
│   │   │   ├── tools/            # Domain tools (fetch, web, database, job, company, skill)
│   │   │   ├── graphs/           # LangGraph workflows
│   │   │   └── prompts/          # Centralized prompt registry
│   │   └── logging.py            # Structured agent events
│   ├── dependencies.py           # FastAPI dependency injection
│   ├── exceptions.py             # Exception hierarchy
│   └── tests/                    # 376+ tests by bounded context
│       ├── ai/
│       ├── jobs/
│       ├── companies/
│       ├── skills/
│       ├── career/
│       ├── processing/
│       ├── shared/
│       └── migration/
└── client/
    └── src/
        ├── features/             # Feature-based architecture
        │   ├── jobs/             # Job processing (components, hooks, tests)
        │   ├── companies/        # Company intelligence
        │   ├── insights/         # Career insights
        │   ├── skills/           # Skills management + roadmaps
        │   ├── resume/           # Resume generation
        │   └── rules/            # Scoring rules
        ├── shared/               # Shared components, hooks, UI, lib
        │   ├── components/       # ProcessingItem, GenerationProgressCard, NotesLinksInput
        │   ├── hooks/            # useSocketIO, usePending, useWorkflow, useToast
        │   ├── lib/              # utils, skills helpers
        │   └── ui/               # shadcn/ui components (15 primitives)
        ├── layout/               # Header, Sidebar
        ├── App.tsx               # Root app
        └── main.tsx              # Entry point
```

## Testing

```bash
# Backend (376+ tests)
uv run pytest app/server/tests/ -v

# AI layer (70 tests)
uv run pytest tests/test_ai/ -v

# All backend tests
uv run pytest tests/test_ai/ app/server/tests/ -v

# Frontend (23 tests)
cd app/client && npx vitest run
```

## Documentation

- `docs/README.md` — Documentation index
- `docs/architecture/ARCHITECTURE.md` — System design, DDD contexts, entities, data flows
- `docs/CHANGELOG.md` — Version history
- `docs/AI_ARCHITECTURE.md` — Provider abstraction, agents, tools, LangGraph workflows
- `docs/API.md` — Complete REST API and WebSocket reference
- API docs at runtime: `/api/docs` (Swagger UI), `/api/redoc` (ReDoc)
