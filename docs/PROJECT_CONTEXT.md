# Project Context — Job Search Intelligence

## 1. Project Overview

**Name**: Job Search Intelligence
**Purpose**: AI-powered career platform for software engineers seeking visa-sponsored roles in Europe (Germany, Netherlands)
**Target Users**: Software engineers, career changers, job seekers
**Core Problems Solved**: Job discovery, company analysis, skill gap identification, resume generation, career insights

## 2. Product Structure

### Jobs
- **Responsibility**: Job discovery, processing, scoring
- **Features**: URL submission, fetch/extract/analyze pipeline, real-time progress, configurable scoring
- **Files**: `features/jobs/`, `services/worker.py`, `blueprints/pending.py`

### Companies
- **Responsibility**: Company intelligence and analysis
- **Features**: Multi-source input (notes+links), profile extraction, visa assessment, Fit/Success/Overall scoring
- **Files**: `features/companies/`, `services/company_worker.py`, `blueprints/companies.py`

### Skills (Top-level)
- **Responsibility**: Skill management center — CRUD, categories, roadmaps, progress
- **Features**: 5-category taxonomy, aliases/merge, roadmap generation, progress tracking
- **Files**: `features/skills/`, `blueprints/tech_stack.py`, `blueprints/skill_roadmaps.py`

### Insights
- **Responsibility**: Career intelligence analysis
- **Features**: Per-section generation (overview, skills, opportunities, companies, market, networking)
- **Files**: `features/insights/`, `services/insights.py`, `blueprints/insights.py`

### Settings
- **Resume**: AI-powered resume/cover letter generation with progress bars
- **Rules**: Configurable scoring rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING)

## 3. Technology Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **UI**: shadcn/ui + Tailwind CSS (custom tokens: text-3xs, text-2xs)
- **State**: React hooks (useState, useCallback, useRef)
- **Data fetching**: Direct fetch() calls + WebSocket (SocketIO)
- **Architecture**: Feature-based (`features/`, `shared/`, `layout/`)

### Backend
- **Framework**: Flask 3.1 with Flask-SocketIO
- **Language**: Python 3.14+
- **Architecture**: Blueprint-based (10 blueprints), service layer
- **Libraries**: structlog, python-dotenv, typer, rich, langgraph, langchain-core

### Database
- **Engine**: SQLite + SQLAlchemy ORM + Alembic migrations
- **Key Tables**: jobs, companies, company_intelligence, skills, skill_roadmaps, career_insights, pending_jobs, pending_companies, pending_generations
- **Migrations**: Alembic migration scripts

### AI Layer
- **LLMService**: Unified entry point for all AI calls
- **Providers**: Mimo (production), OpenAI (stub), Local LLM (stub)
- **Agents**: Thin orchestration layers over existing services
- **Tools**: Domain services wrapping existing business logic
- **Graphs**: LangGraph-based composable workflows

### Infrastructure
- **Deployment**: Single `./start` (FastAPI + Vite dev server)
- **CI/CD**: GitHub Actions (pytest + vitest)
- **Monitoring**: structlog to `app/server/logs/`

## 4. Architecture Summary

```
React SPA → Flask API → SQLite DB
     ↓           ↓
  WebSocket   AI Agent Layer (LLMService)
                    ↓
              Provider Layer (Mimo / OpenAI / Local)
```

- **Frontend** communicates via HTTP (REST) + WebSocket (real-time)
- **Backend** uses Blueprint-based routing, service layer for business logic
- **AI** via LLMService provider abstraction (Mimo CLI default)
- **Queue**: Single shared queue for jobs + companies with concurrency control

## 5. Domain Model

### Job → Company (many-to-one)
- Jobs link to companies via `company_id` column
- Jobs have scoring: `fit_score`, `success_score`, `overall_score`

### Skill → Skill (many-to-many via aliases/relationships)
- Skills have categories, confidence, market_relevance
- Aliases merge duplicate skills (Postgres → PostgreSQL)
- Relationships: related, similar, parent, child, alternative

### Skill → Roadmap (one-to-many)
- Each skill can have multiple roadmap versions
- Roadmaps are hierarchical trees with progress tracking

### Job → Skill (implicit via stack column)
- Jobs contain `stack` column with comma-separated skills
- Skills intelligence analyzes this to extract market demand

### Job → Generation (one-to-many)
- Jobs can have multiple resume/cover generations
- Generations tracked in `pending_generations` with progress

## 6. AI Architecture

### LLMService
- Unified entry point for all AI calls
- Methods: generate(), generate_structured(), generate_streaming()
- Accessed via: `from ai_compat import get_llm_service`

### Providers
- MimoProvider: Wraps Mimo CLI subprocess
- OpenAIProvider: Stub for OpenAI API
- LocalLLMProvider: Stub for Ollama/local LLMs
- Selection via `AI_PROVIDER` env var

### Agents
- Thin orchestration layers over existing services
- Use tools for business operations
- State passing via AgentState dict

### Workflow Graphs
- JobProcessingGraph: fetch → validate → extract → score
- CompanyProcessingGraph: fetch → extract → analyze → save
- InsightsGenerationGraph: overview → opportunities → companies → market → networking → skills_intel

### Existing Prompts
- `prompts/insights/` — 7 prompts for career intelligence sections
- `prompts/skill_roadmaps/` — 4 prompts for roadmap generation/extension
- `prompts/job_processing/` — 4 prompts for job extraction
- `prompts/company/` — 2 prompts for company analysis
- `prompts/resume/` — 2 prompts for resume/cover generation

## 7. Development Rules

### Must Follow
- TypeScript for all frontend code (no .js/.jsx)
- Feature-based architecture (`features/`, `shared/`, `layout/`)
- SQLAlchemy ORM for all database access
- structlog for logging (no print())
- Single generation lock (one AI analysis at a time)
- Version tracking for retries
- LLMService for all AI calls (never MimoRunner directly)
- DDD, SOLID, TDD, Design Patterns

### Must Not
- Add paid API dependencies
- Use raw SQL (use SQLAlchemy ORM instead)
- Add routes in `app.py`
- Create duplicate prompt systems
- Mix feature boundaries
- Call MimoRunner directly

## 8. Technical Debt

- `_db()` sets `row_factory=None` but some callers use `dict(r)` — inconsistent
- `pending_jobs.notes` and `pending_jobs.links` columns added but job worker doesn't fully iterate them yet
- `skill_relationships` table exists but never populated by production code
- Some test fixtures missing `version` column
