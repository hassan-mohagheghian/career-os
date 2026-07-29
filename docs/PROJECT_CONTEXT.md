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
- **Files**: `app/server/jobs/` (domain, application, infrastructure, presentation), `features/jobs/`

### Companies
- **Responsibility**: Company intelligence and analysis
- **Features**: Multi-source input (notes+links), profile extraction, visa assessment, Fit/Success/Overall scoring
- **Files**: `app/server/companies/`, `features/companies/`

### Skills (Top-level)
- **Responsibility**: Skill management center — CRUD, categories, roadmaps, progress
- **Features**: 5-category taxonomy, aliases/merge, roadmap generation, progress tracking
- **Files**: `app/server/skills/`, `features/skills/`

### Insights
- **Responsibility**: Career intelligence analysis
- **Features**: Per-section generation (overview, skills, opportunities, companies, market, networking)
- **Files**: `app/server/career/`, `features/insights/`

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
- **Framework**: FastAPI with python-socketio
- **Language**: Python 3.14+
- **Architecture**: DDD modular monolith — 8 bounded contexts (Jobs, Companies, Skills, Career, Resume, AI, Pending, Shared)
- **Libraries**: SQLAlchemy ORM + Alembic, structlog, pydantic-v2, python-dotenv, typer, rich, langgraph, langchain-core

### Database
- **Engine**: SQLite + SQLAlchemy ORM + Alembic migrations
- **Key Tables**: jobs, companies, company_intelligence, skills, skill_roadmaps, pending_jobs, pending_companies, pending_generations
- **Migrations**: Alembic migration scripts

### AI Layer
- **LLMService**: Unified entry point for all AI calls
- **Providers**: Mimo (production), OpenAI (stub), Local LLM (stub), Gemini, OpenCode, AGY, Mock (testing)
- **Agents**: LangGraph-based workflow orchestration with state management
- **Tools**: Domain services wrapping existing business logic (fetch, web, database, job, company, skill, resume)
- **Graphs**: LangGraph-based composable workflows (JobProcessing, CompanyProcessing, InsightsGeneration, ResumeGeneration, SkillExtraction, SkillRoadmap)

### Infrastructure
- **Deployment**: Single `./start` (FastAPI + Vite dev server)
- **CI/CD**: GitHub Actions (pytest + vitest)
- **Monitoring**: structlog to `app/server/logs/`

## 4. Architecture Summary

```
React SPA → FastAPI → SQLite DB (SQLAlchemy ORM)
     ↓           ↓
  WebSocket   AI Agent Layer (LLMService + LangGraph)
                    ↓
         Provider Layer (Mimo / OpenAI / Local / Gemini)
```

- **Frontend** communicates via HTTP (REST) + WebSocket (real-time)
- **Backend** uses DDD modular monolith — 8 bounded contexts with FastAPI routers
- **AI** via LLMService provider abstraction (Mimo CLI default) with LangGraph workflow graphs
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
