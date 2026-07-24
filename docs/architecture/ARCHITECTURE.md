# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    React SPA (Vite)                      │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │  Jobs   │ │Companies │ │Career Int│ │ Intelligence│  │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘  │
│       └───────────┴────────────┴──────────────┘         │
│                    Hash-based routing                     │
└─────────────────────────┼───────────────────────────────┘
                          │ HTTP/WebSocket
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

**Stack**: React 18 (JSX) + Vite + shadcn/ui + Tailwind | Flask + SQLite (raw SQL) + Mimo CLI subprocess | WebSocket + SSE

## Core Entities

| Entity | Table | Purpose |
|--------|-------|---------|
| Job | `jobs` | Processed postings with scores (fit_score, success_score, overall_score) |
| Company | `companies` | Profiles with industry, tech_stack, funding_stage |
| Company Intelligence | `company_intelligence` | AI analysis per company |
| Resume | `resumes` | Master, tailored, cover letters, LinkedIn |
| Preferences | `preferences` | Configurable scoring rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING) |
| Career Insights | `career_insights` | Versioned intelligence results (overview, opportunities, companies, skills, market, networking) |
| Career Insight Runs | `career_insight_runs` | Generation workflow tracking |
| Tech Stack | `tech_stack` | Skills with category, confidence, market_relevance, source |
| Skill Aliases | `skill_aliases` | Merged skill variants (canonical skill_id → alias_name) |
| Skill Relationships | `skill_relationships` | Related, similar, parent, child, alternative links |
| Skill Roadmaps | `skill_roadmaps` | Hierarchical learning trees per skill |
| Skill Roadmap Progress | `skill_roadmap_progress` | User completion tracking |
| Skill Roadmap Jobs | `skill_roadmap_jobs` | Generation job status |

```
jobs ── company ── company_intelligence
  │                  └── company_links
  ├── summaries
  └── resumes (via job_num)

career_insight_runs ── career_insights

tech_stack ── skill_aliases (merged variants)
           ── skill_relationships (related/similar/parent/child)
           ── skill_roadmaps ── skill_roadmap_progress
                            ── skill_roadmap_jobs
```

## Backend Modules

| Blueprint | File | Purpose |
|-----------|------|---------|
| jobs | `blueprints/jobs.py` | Job CRUD, rescore, requeue |
| pending | `blueprints/pending.py` | Processing queue |
| companies | `blueprints/companies.py` | Company CRUD |
| intelligence | `blueprints/intelligence.py` | Existing analysis |
| career_intel | `blueprints/career_intel.py` | Career intelligence |
| resumes | `blueprints/resumes.py` | Resume/cover generation |
| rules | `blueprints/rules.py` | Scoring config |
| dashboard | `blueprints/dashboard.py` | Tech stack, skill roadmaps, skill management |

| Service | File | Purpose |
|---------|------|---------|
| worker | `services/worker.py` | Job processing pipeline (WebSocket events) |
| company_worker | `services/company_worker.py` | Company processing (WebSocket events) |
| career_intel | `services/career_intel.py` | Career intelligence (concurrency-locked) |
| process/* | `services/process/` | Broadcaster, models, mimo_runner, process_manager |

## Prompt Organization

| Directory | Prompts |
|-----------|---------|
| `career_intel/` | career_intelligence.txt (combined), overview_intelligence.txt, opportunities_intelligence.txt, companies_intelligence.txt, skills_intelligence.txt, market_intelligence.txt, networking_intelligence.txt |
| `skill_roadmaps/` | skill_roadmaps.txt, extend, finegrain, generate |
| `job_processing/` | step2_validate, step3_extract_raw, step4_extract_struct, step8_score |
| `company/` | company_extract.txt, company_analyze.txt |
| `resume/` | step_resume_generate.txt, step7_cover_generate.txt |

## Frontend

**Pages**: JobsPage, CompaniesPage, ResumeTab, CareerIntelTab, IntelligenceTab, RulesTab
**Hooks**: useJobs, usePending, useCompanies, useIntelligence, useCareerIntel, useResume, useWorkflow, useSocketIO

**Key Components**:
- `SkillsIntelSection` — Category tabs, merge DnD, alias badges, collapsible add skill
- `SkillDetailDrawer` — Rename, checkable roadmap, merged variants, relationships
- `SkillRoadmapDrawer` — Roadmap tree with progress tracking
- `ProcessingItem` / `CompanyProcessingItem` — Real-time processing cards
- `GenerationProgressCard` — Shared progress card with session_id

## Test Structure

```
tests/
├── conftest.py                    # Shared test_db fixture
├── test_blueprints/               # mirrors server/blueprints/
│   ├── test_dashboard.py
│   ├── test_roadmap_helpers.py
│   └── test_blueprints.py
├── test_core/                     # mirrors server/core/
│   └── test_queue.py
├── test_process/                  # cross-cutting tests
│   └── test_skill_management.py   # merge, taxonomy, aliases, relationships
└── test_services/                 # mirrors server/services/
    ├── test_worker_broadcast.py
    ├── test_company_worker.py
    ├── test_worker_utils.py
    └── test_process/              # mirrors server/services/process/
        ├── test_broadcaster.py
        ├── test_models.py
        ├── test_process_manager.py
        ├── test_repository.py
        ├── test_temp_manager.py
        └── test_worker_base.py
```

## Data Flows

### Job Processing
URL → pending_jobs → Fetch → Extract Raw → Extract Structured → Analyze & Score → Summary → Save to DB → WebSocket `pending:update`/`pending:log`/`pending:complete` streams to frontend

### Career Intelligence (concurrency-locked, one at a time)

**Generate All:** User clicks Generate → Lock acquired → Combined prompt (`career_intelligence.txt`) runs → All 6 sections saved to `career_insights` (skills saved as `skills_intel`) → Lock released → WebSocket `career_intel:progress` with session_id

**Single Section Refresh:** User clicks Refresh on tab → Lock acquired → Section-specific prompt runs (e.g. `overview_intelligence.txt`) → Only that section saved → Lock released → WebSocket `career_intel:progress`

**Skills Tab:** Uses dedicated `skills_intelligence.txt` prompt (full report with learning roadmap, readiness score, recommendations) — same prompt for both single refresh and Generate All

### Skill Management
User adds/merges/hides/renames skills → tech_stack updated → skill_aliases created for merges → skill_roadmaps renamed → WebSocket `skill_roadmap:update` broadcasts

### Scoring
Job + Company data → SHARED rules → JOB rules → COMPANY_PRODUCT rules → COMPANY_RECRUITING rules → fit_score (weighted avg) + success_score (weighted avg) → overall_score = fit × 0.6 + success × 0.4

## Key Patterns
1. Blueprint architecture per feature
2. Prompt templates in subdirectories with `{variable}` interpolation
3. Background threading for long operations
4. WebSocket for real-time processing (pending, career-intel, skill-roadmaps)
5. Concurrency lock for career intelligence (single-run enforcement)
6. Broadcaster pattern for SocketIO event delivery with `[ws]` logging
7. Skill aliases via `skill_aliases` table (canonical + variant records)
8. Category taxonomy: technical, engineering, professional, domain, career

## Coding Standards

### Backend (Python / Flask)

All backend code follows **OOP, SOLID, Design Patterns, System Design, DDD, and TDD**.

| Principle | How We Apply It |
|-----------|-----------------|
| **OOP** | Entities are modeled as classes or typed dicts. Services are instantiated, not a bag of functions. |
| **SOLID — SRP** | Each module has one reason to change: `blueprints/` handles HTTP, `services/` handles business logic, `core/` handles DB/queue. |
| **SOLID — OCP** | New insight types or pipeline steps are added by extending, not modifying existing code. |
| **SOLID — LSP** | Interfaces (`IMimoRunner`, `IProcessManager`, `IBroadcaster`) are implemented by concrete classes that are interchangeable. |
| **SOLID — ISP** | Interfaces are narrow: `IPendingRepository` vs `IJobRepository` — callers depend only on what they use. |
| **SOLID — DIP** | Workers depend on abstractions (`interfaces.py`), not on SQLite or SocketIO directly. |
| **Design Patterns** | Strategy (process managers), Repository (DB access), Observer/Broadcaster (WebSocket events), Singleton (ProcessManager), Factory (prompt loading). |
| **System Design** | Concurrency locks for single-run enforcement, process groups for clean subprocess cancellation, thread-safe timeouts, room-based SocketIO broadcasting. |
| **DDD** | Domain logic lives in service modules (`career_intel.py`, `mimo_runner.py`), not in blueprints. Bounded contexts: Job Processing, Company Intelligence, Career Intelligence, Skill Management. Repository pattern abstracts persistence. |
| **TDD** | Tests written before implementation. Domain logic extracted into testable pure functions. Test structure mirrors source: `tests/test_services/`, `tests/test_blueprints/`, `tests/test_core/`. |

**Rule**: Never use raw `subprocess.Popen` when `MimoRunner` exists. Never put business logic in blueprints. Never skip tests for domain logic.

### Frontend (React / JSX)

All frontend code follows **feature-based architecture**.

| Principle | How We Apply It |
|-----------|-----------------|
| **Feature-based structure** | Each feature is a directory: `components/career-intel/`, `components/shared/`. Components, hooks, and domain logic co-locate by feature. |
| **Domain logic in `lib/`** | Pure functions extracted from components live in `lib/skills.js`, `lib/utils.js` — testable without React. |
| **Hooks for state** | Each feature has a dedicated hook (`useCareerIntel`, `useCompanies`, `usePending`) that encapsulates API calls, WebSocket listeners, and state. |
| **Single responsibility** | Components do one thing: `SkillsIntelSection` displays skills, `SkillRoadmapDrawer` shows roadmaps, `SkillDetailDrawer` shows detail. |
| **Shared components** | Cross-feature UI lives in `components/shared/`: `GenerationProgressCard`, `ProcessedCards`. |

**Rule**: Never put API calls or WebSocket logic inside components. Never create monolithic page components — split by feature. Always extract pure domain logic into `lib/` for testability.

### Test Conventions

| Layer | Framework | Location | Convention |
|-------|-----------|----------|------------|
| Backend unit | pytest | `tests/test_services/` | Mirror source structure. Mock external deps (mimo, DB). |
| Backend integration | pytest | `tests/test_blueprints/` | Use `test_db` fixture (temp SQLite). Test HTTP endpoints. |
| Frontend unit | vitest | `src/__tests__/` or `__tests__/` co-located | Test pure domain functions. Test component rendering. |
| Domain logic | Both | Extracted to `lib/` (FE) or service modules (BE) | Must be testable without infrastructure. |
