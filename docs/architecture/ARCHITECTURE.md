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
| `career_intel/` | career_intelligence.txt, skills_intelligence.txt |
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
User clicks Generate → Lock acquired → Collect data (jobs, companies, skills, preferences) → Mimo CLI generates JSON → Save each section to career_insights → Lock released → WebSocket `career_intel:progress` with session_id

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
