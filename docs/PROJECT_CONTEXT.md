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

### Networking
- **Responsibility**: Connection strategy (part of Insights)
- **Features**: LinkedIn targets, outreach templates, company prioritization

### Settings
- **Resume**: AI-powered resume/cover letter generation
- **Rules**: Configurable scoring rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING)

## 3. Technology Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **UI**: shadcn/ui + Tailwind CSS (custom tokens: text-3xs, text-2xs)
- **State**: React hooks (useState, useCallback, useRef)
- **Data fetching**: Direct fetch() calls
- **Architecture**: Feature-based (`features/`, `shared/`, `layout/`)

### Backend
- **Framework**: Flask 3.1 with Flask-SocketIO
- **Language**: Python 3.15+
- **Architecture**: Blueprint-based (10 blueprints), service layer
- **Libraries**: structlog, python-dotenv, typer, rich

### Database
- **Engine**: SQLite (raw SQL, no ORM)
- **Key Tables**: jobs, companies, company_intelligence, tech_stack, skill_roadmaps, career_insights, pending_jobs, pending_companies
- **Migrations**: Inline system in `core/db.py` + `migrations.py`

### Infrastructure
- **Deployment**: Single `./start.sh` (Flask + Vite dev server)
- **CI/CD**: GitHub Actions (pytest + vitest)
- **Monitoring**: structlog to `app/server/logs/`

## 4. Architecture Summary

```
React SPA → Flask API → SQLite DB
     ↓           ↓
  WebSocket   Mimo CLI (AI)
```

- **Frontend** communicates via HTTP (REST) + WebSocket (real-time)
- **Backend** uses Blueprint-based routing, service layer for business logic
- **AI** via Mimo CLI subprocess (no paid APIs)
- **Queue**: Single shared queue for jobs + companies with concurrency control

## 5. Domain Model

### Job → Company (many-to-one)
- Jobs link to companies via `company` name column
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

## 6. AI Architecture

### Existing Prompts
- `insights/` — 7 prompts for career intelligence sections
- `skill_roadmaps/` — 4 prompts for roadmap generation/extension
- `job_processing/` — 4 prompts for job extraction
- `company/` — 2 prompts for company analysis

### AI Tools
- `MimoRunner` — subprocess management with streaming, session support
- `ProcessManager` — lifecycle management for background tasks

### Workflows
- Job: fetch → extract → validate → score → save
- Company: fetch → extract → analyze → save
- Insights: per-section generation with concurrency lock
- Roadmap: generate → extend → finegrain per skill

## 7. Development Rules

### Must Follow
- TypeScript for all frontend code (no .js/.jsx)
- Feature-based architecture (`features/`, `shared/`, `layout/`)
- Raw SQL (no ORM)
- structlog for logging (no print())
- Single generation lock (one AI analysis at a time)
- Version tracking for retries

### Must Not
- Add paid API dependencies
- Use ORM
- Add routes in `app.py`
- Create duplicate prompt systems
- Mix feature boundaries

## 8. Technical Debt

- `_db()` sets `row_factory=None` but some callers use `dict(r)` — inconsistent
- `pending_jobs.notes` and `pending_jobs.links` columns added but job worker doesn't fully iterate them yet
- Skills intelligence AI report not propagated to `tech_stack` DB (only stored as JSON blob)
- `skill_relationships` table exists but never populated by production code
- Some test fixtures missing `version` column
