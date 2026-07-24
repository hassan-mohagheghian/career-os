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
| Backend | Python Flask, SQLite (raw SQL), Flask-SocketIO |
| Frontend | React 18 (JSX), Vite, shadcn/ui, Tailwind CSS |
| AI | Mimo CLI subprocess |
| Realtime | WebSocket (SocketIO, threading mode) |
| Testing | pytest (224 tests), vitest |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React SPA (Vite)                      │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │  Jobs   │ │Companies │ │Career Int│ │ Intelligence│  │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘  │
│       └───────────┴────────────┴──────────────┘         │
│                    Hash-based routing                     │
└─────────────────────────┼───────────────────────────────┘
                          │ HTTP + WebSocket
┌─────────────────────────┼───────────────────────────────┐
│                   Flask API (port 5000)                   │
│              ┌──────────▼──────────┐                     │
│              │     SQLite DB       │                     │
│              │   (jobs.db)         │                     │
│              └─────────────────────┘                     │
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

### Company Intelligence
- Company profile extraction and analysis
- Product vs Recruiting classification
- Visa friendliness assessment

### Skill Management
- **5 Categories**: Technical, Engineering, Professional, Domain, Career
- **Skill Aliases**: Merge duplicate skills (e.g., Postgres → PostgreSQL)
- **Drag-and-Drop Merge**: Combine skills across all sections
- **Checkable Roadmaps**: Track learning progress per skill
- **Auto-categorization**: AI categorizes skills from job analysis

### Career Intelligence
- Career health score (0-100)
- Strengths, gaps, learning recommendations
- Market analysis (countries, cities, remote)
- Real-time progress with session tracking

### Resume Generation
- AI-powered resume tailoring
- Cover letter generation
- LinkedIn profile integration

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/pending` | GET/POST | Job queue management |
| `/api/tech-stack` | GET/POST | Skills CRUD |
| `/api/tech-stack/:id/hide` | PATCH | Hide skill |
| `/api/tech-stack/:id/rename` | PATCH | Rename skill |
| `/api/tech-stack/merge` | POST | Merge skills |
| `/api/career-intelligence` | GET | Career insights |
| `/api/career-intelligence/progress` | GET | Real-time progress |
| `/api/skill-roadmaps` | GET/POST | Learning roadmaps |

## WebSocket Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `pending:update` | Server→Client | Job step progress |
| `pending:log` | Server→Client | Job processing logs |
| `pending:complete` | Server→Client | Job finished |
| `career_intel:progress` | Server→Client | Career analysis progress |
| `skill_roadmap:update` | Server→Client | Roadmap generation status |

## Project Structure

```
app/
├── server/
│   ├── app.py                    # Flask entry point
│   ├── blueprints/               # API routes (jobs, companies, career_intel, dashboard)
│   ├── services/                 # Business logic (worker, company_worker, career_intel)
│   │   └── process/              # Broadcaster, models, mimo_runner, process_manager
│   ├── core/                     # DB schema, queue manager
│   ├── prompts/                  # AI prompt templates (organized by feature)
│   │   ├── career_intel/
│   │   ├── skill_roadmaps/
│   │   ├── job_processing/
│   │   ├── company/
│   │   └── resume/
│   └── tests/                    # Mirror server structure
│       ├── test_blueprints/
│       ├── test_services/
│       ├── test_core/
│       └── test_process/
└── client/
    └── src/
        ├── components/
        │   ├── career-intel/     # Skills, Market, Networking tabs
        │   ├── companies/        # Company processing
        │   ├── jobs/             # Job cards and drawer
        │   └── shared/           # ProcessingItem, GenerationProgressCard
        └── hooks/                # usePending, useCompanies, useCareerIntel, useSocketIO
```

## Testing

```bash
cd app/server
python -m pytest tests/ -v
```

224 tests covering: broadcaster, worker, company_worker, skill management, models, process_manager, queue, repository, roadmaps, blueprints.

## Documentation

See `docs/` for detailed documentation:
- `docs/ARCHITECTURE.md` — System design, entities, data flows
- `docs/CHANGELOG.md` — Version history
- `docs/ROADMAP.md` — Completed features and future plans
- `docs/worker-architecture.md` — Processing pipeline design
