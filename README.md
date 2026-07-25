# Job Search Intelligence

AI-powered career intelligence platform for engineers — job discovery, company analysis, skill management, resume generation, and career insights. Built for visa-sponsored roles in Europe (Germany, Netherlands).

## Quick Start

```bash
./start.sh
```

Opens Flask API (port 5000) + React dev server (port 5173).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.15+, Flask 3.1, SQLite (raw SQL), Flask-SocketIO |
| Frontend | React 18, TypeScript, Vite 6, shadcn/ui, Tailwind CSS |
| AI | Mimo CLI subprocess |
| Realtime | WebSocket (SocketIO, threading mode) |
| Testing | pytest (267 tests), vitest (23 tests) |
| API Docs | Swagger UI (`/api/docs/`), ReDoc (`/api/redoc/`) |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  React SPA (Vite + TypeScript)            │
│  ┌──────┐ ┌──────────┐ ┌─────────┐ ┌────────┐ ┌──────┐│
│  │ Jobs │ │Companies │ │Insights │ │ Skills │ │Resume││
│  └──┬───┘ └────┬─────┘ └────┬────┘ └───┬────┘ └──┬───┘│
│     └──────────┴────────────┴──────────┴─────────┘     │
│                  Hash-based routing                      │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP + WebSocket
┌─────────────────────────┼───────────────────────────────┐
│                 Flask API (port 5000)                     │
│            ┌────────────▼────────────┐                   │
│            │      SQLite DB          │                   │
│            │      (jobs.db)          │                   │
│            └─────────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │    Mimo CLI (AI)      │
              └───────────────────────┘
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

### Skills Intelligence
- **5 Categories**: Technical, Engineering, Professional, Domain, Career
- **Skill Aliases**: Merge duplicate skills (e.g., Postgres → PostgreSQL)
- **Drag-and-Drop Merge**: Combine skills across all sections
- **Checkable Roadmaps**: Track learning progress per skill
- **Auto-categorization**: AI categorizes skills from job analysis
- Independent generation (separate from Insights)

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

### API Documentation
- **Swagger UI**: `http://localhost:5000/api/docs/`
- **ReDoc**: `http://localhost:5000/api/redoc/`
- **OpenAPI Spec**: `http://localhost:5000/api/swagger.json`

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/pending` | GET/POST | Job queue management |
| `/api/tech-stack` | GET/POST | Skills CRUD |
| `/api/tech-stack/:id/hide` | PATCH | Hide skill |
| `/api/tech-stack/:id/rename` | PATCH | Rename skill |
| `/api/tech-stack/merge` | POST | Merge skills |
| `/api/insights` | GET | Career insights |
| `/api/insights/progress` | GET | Real-time progress |
| `/api/skill-roadmaps` | GET/POST | Learning roadmaps |
| `/api/generation-history` | GET | Unified generation history |

## WebSocket Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `pending:update` | Server→Client | Job step progress |
| `pending:log` | Server→Client | Job processing logs |
| `pending:complete` | Server→Client | Job finished |
| `insights:progress` | Server→Client | Insights analysis progress |
| `skill_roadmap:update` | Server→Client | Roadmap generation status |

## Project Structure

```
app/
├── server/
│   ├── app.py                    # Flask entry point
│   ├── blueprints/               # API routes (jobs, companies, insights, tech_stack, etc.)
│   ├── services/                 # Business logic (worker, company_worker, insights)
│   │   └── process/              # Broadcaster, models, mimo_runner, process_manager
│   ├── core/                     # DB schema, queue manager
│   ├── prompts/                  # AI prompt templates (organized by feature)
│   │   ├── insights/             # Career intelligence prompts
│   │   ├── skill_roadmaps/       # Skill roadmap prompts
│   │   ├── job_processing/       # Job processing prompts
│   │   ├── company/              # Company analysis prompts
│   │   └── resume/               # Resume generation prompts
│   └── tests/                    # Mirror server structure
│       ├── test_blueprints/
│       ├── test_services/
│       ├── test_core/
│       └── test_process/
└── client/
    └── src/
        ├── features/             # Feature-based architecture
        │   ├── jobs/             # Job processing (components, hooks)
        │   ├── companies/        # Company intelligence
        │   ├── insights/         # Career insights (formerly career-intel)
        │   ├── skills/           # Skills intelligence (standalone)
        │   ├── resume/           # Resume generation
        │   └── rules/            # Scoring rules
        ├── shared/               # Shared components, hooks, UI, lib
        │   ├── components/       # ProcessingItem, GenerationProgressCard, etc.
        │   ├── hooks/            # useSocketIO, usePending, useWorkflow, useToast
        │   ├── lib/              # utils, skills helpers
        │   └── ui/               # shadcn/ui components
        ├── layout/               # Header, Sidebar
        ├── App.tsx               # Root app
        └── main.tsx              # Entry point
```

## Testing

```bash
# Backend
cd app/server && python -m pytest tests/ -v

# Frontend
cd app/client && npx vitest run
```

267 backend + 23 frontend tests covering: broadcaster, worker, company_worker, skill management, models, process_manager, queue, repository, roadmaps, blueprints, career insights.

## Documentation

- `docs/ARCHITECTURE.md` — System design, entities, data flows
- `docs/CHANGELOG.md` — Version history
- `docs/ROADMAP.md` — Completed features and future plans
- API docs at runtime: `/api/docs/` (Swagger UI), `/api/redoc/` (ReDoc)
