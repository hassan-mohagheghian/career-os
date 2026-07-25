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

**Stack**: React 18 + TypeScript + Vite 6 + shadcn/ui + Tailwind CSS | Flask 3.1 + Python 3.14 + SQLite (raw SQL) | AI Agent Layer (LLMService + LangGraph) | WebSocket (SocketIO, threading mode)

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
│   ├── app.py              Flask entry point, SocketIO, blueprints
│   ├── ai_compat.py        Bridge for server → ai imports
│   ├── config.py           Centralized path constants + AI_PROVIDER
│   ├── database.py         get_db() helper
│   ├── migrations.py       Schema + data migrations
│   ├── blueprints/         API routes (10 blueprints)
│   │   ├── jobs.py         Job CRUD, scoring
│   │   ├── pending.py      Processing queue (accepts notes+links)
│   │   ├── companies.py    Company CRUD, intelligence
│   │   ├── insights.py     Career intelligence endpoints
│   │   ├── tech_stack.py   Skills CRUD, merge, taxonomy
│   │   ├── skill_roadmaps.py  Roadmap generation, progress
│   │   ├── resumes.py      Resume/cover letter generation
│   │   ├── rules.py        Scoring rules
│   │   ├── misc.py         Generation history, dashboard
│   │   ├── api_docs.py     Swagger UI + ReDoc
│   │   └── static.py       SPA static serving
│   ├── services/
│   │   ├── worker.py       Job processing pipeline (uses LLMService)
│   │   ├── company_worker.py  Company processing (uses LLMService)
│   │   ├── insights.py     Career intelligence (uses LLMService)
│   │   └── process/        Broadcaster, models, process_manager
│   ├── core/
│   │   ├── db.py           DB schema, migrations
│   │   └── queue.py        Job queue manager (shared for jobs + companies)
│   ├── prompts/            AI prompt templates
│   │   ├── insights/       Career intelligence (7 prompts)
│   │   ├── skill_roadmaps/ Skill roadmap generation
│   │   ├── job_processing/ Job processing steps
│   │   ├── company/        Company analysis
│   │   └── resume/         Resume generation
│   └── tests/              306 tests mirroring server structure
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

- **No ORM**: Raw SQL for full control over queries and schema
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
