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
| Backend | Python 3.15+, Flask 3.1, SQLite (raw SQL), Flask-SocketIO |
| Frontend | React 18, TypeScript, Vite 6, shadcn/ui, Tailwind CSS |
| AI | Mimo CLI subprocess |
| Realtime | WebSocket (SocketIO, threading mode) |
| Testing | pytest (306 tests), vitest (23 tests) |
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
│   ├── blueprints/               # API routes (10 blueprints)
│   ├── services/                 # Business logic (worker, company_worker, insights)
│   │   └── process/              # Broadcaster, models, mimo_runner, process_manager
│   ├── core/                     # DB schema, queue manager
│   ├── prompts/                  # AI prompt templates (organized by feature)
│   │   ├── insights/             # Career intelligence prompts (7)
│   │   ├── skill_roadmaps/       # Skill roadmap prompts (4)
│   │   ├── job_processing/       # Job processing prompts (4)
│   │   ├── company/              # Company analysis prompts (2)
│   │   └── resume/               # Resume generation prompts (2)
│   └── tests/                    # 306 tests mirroring server structure
│       ├── test_blueprints/
│       ├── test_services/
│       ├── test_core/
│       └── test_process/
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
# Backend (306 tests)
cd app/server && python -m pytest tests/ -v

# Frontend (23 tests)
cd app/client && npx vitest run
```

## Documentation

- `docs/README.md` — Documentation index
- `docs/architecture/ARCHITECTURE.md` — System design, entities, data flows
- `docs/CHANGELOG.md` — Version history
- API docs at runtime: `/api/docs/` (Swagger UI), `/api/redoc/` (ReDoc)
