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

**Stack**: React 18 + TypeScript + Vite 6 + shadcn/ui + Tailwind CSS | Flask 3.1 + SQLite (raw SQL) + Mimo CLI subprocess | WebSocket (SocketIO, threading mode)

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
| Tech Stack | `tech_stack` | Skills with category, confidence, market_relevance, source |
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

tech_stack ── skill_aliases
  ├── skill_relationships
  ├── skill_roadmaps ── skill_roadmap_progress
  └── skill_roadmap_jobs
```

## Feature-Based Frontend Architecture

```
src/
├── features/
│   ├── jobs/           Job processing (components, hooks, tests)
│   ├── companies/      Company intelligence
│   ├── insights/       Career insights (formerly career-intel)
│   ├── skills/         Skills intelligence (standalone)
│   ├── resume/         Resume generation
│   └── rules/          Scoring rules
├── shared/
│   ├── components/     Shared UI (ProcessingItem, GenerationProgressCard, etc.)
│   ├── hooks/          Shared hooks (useSocketIO, usePending, useWorkflow, useToast)
│   ├── lib/            Utilities (cn, resolveSkillCategory)
│   └── ui/             shadcn/ui components (15 primitives)
├── layout/             Header, Sidebar
├── App.tsx             Root app
└── main.tsx            Entry point
```

## Backend Structure

```
app/server/
├── app.py              Flask entry point, SocketIO, blueprints
├── config.py           Centralized path constants
├── database.py         get_db() helper
├── migrations.py       Schema + data migrations
├── blueprints/         API routes (10 blueprints)
│   ├── jobs.py         Job CRUD, scoring
│   ├── pending.py      Processing queue
│   ├── companies.py    Company CRUD, intelligence
│   ├── insights.py     Career intelligence endpoints
│   ├── tech_stack.py   Skills CRUD, merge, taxonomy
│   ├── skill_roadmaps.py  Roadmap generation, progress
│   ├── resumes.py      Resume/cover letter generation
│   ├── rules.py        Scoring rules
│   ├── misc.py         Generation history, dashboard
│   ├── api_docs.py     Swagger UI + ReDoc
│   └── static.py       SPA static serving
├── services/
│   ├── worker.py       Job processing pipeline
│   ├── company_worker.py  Company processing
│   ├── insights.py     Career intelligence (concurrency-locked)
│   └── process/        Broadcaster, models, mimo_runner, process_manager
├── core/
│   ├── db.py           DB schema, migrations
│   └── queue.py        Job queue manager
├── prompts/            AI prompt templates
│   ├── insights/       Career intelligence (7 prompts)
│   ├── skill_roadmaps/ Skill roadmap generation
│   ├── job_processing/ Job processing steps
│   ├── company/        Company analysis
│   └── resume/         Resume generation
└── tests/              267 tests mirroring server structure
```

## Navigation Tabs

| Tab | Section | Sub-tabs | Description |
|-----|---------|----------|-------------|
| Jobs | jobs | — | Job processing queue + processed cards |
| Companies | jobs | — | Company intelligence + processing |
| **Skills** | analysis | — | Skills intelligence (standalone) |
| Resume | settings | — | Resume/cover letter generation |
| Insights | analysis | overview, opportunities, companies, market, networking | Career intelligence analysis |
| Rules | settings | — | Scoring rules configuration |

**Note**: Skills is a top-level tab, separate from Insights. Career Intel was renamed to Insights.

## Data Flow

### Job Processing
```
URL → pending_jobs → worker.py → fetch → extract → analyze → score → save to jobs
```

### Company Processing
```
Notes/URLs → pending_companies → company_worker.py → fetch → extract → analyze → save to companies
```

### Insights Generation
```
Click Generate → insights.py → per-section prompts → mimo CLI → save to career_insights
```

### Skills Intelligence
```
Click Generate → insights.py → skills_intelligence prompt → mimo CLI → save to career_insights (skills_intel)
```

## WebSocket Events

| Event | Room | Purpose |
|-------|------|---------|
| `pending:update` | — | Job step progress |
| `pending:log` | — | Job processing logs |
| `pending:complete` | — | Job finished |
| `company:update` | — | Company processing progress |
| `insights:progress` | insights | Insights generation progress |
| `skill_roadmap:update` | skills | Per-skill roadmap generation |

## Design Decisions

- **No ORM**: Raw SQL for full control over queries and schema
- **Feature-based frontend**: Each feature owns its components, hooks, and types
- **Concurrency lock**: Only one insights generation at a time
- **Version tracking**: `version` column on pending_jobs/companies for retry counting
- **Stale run recovery**: On startup, stuck `processing` jobs are marked `failed`
- **Font size system**: Custom Tailwind tokens `text-3xs` (6px) and `text-2xs` (8px) for dense dashboard UI
- **API docs**: Static OpenAPI 3.0 spec served via Swagger UI (`/api/docs/`) and ReDoc (`/api/redoc/`)
