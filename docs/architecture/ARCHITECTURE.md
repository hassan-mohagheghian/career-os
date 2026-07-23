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

```
jobs ── company ── company_intelligence
  │                  └── company_links
  ├── summaries
  └── resumes (via job_num)

career_insight_runs ── career_insights
```

## Backend Modules

| Blueprint | File | Purpose |
|-----------|------|---------|
| jobs | `blueprints/jobs.py` | Job CRUD, rescore, requeue |
| pending | `blueprints/pending.py` | Processing queue |
| companies | `blueprints/companies.py` | Company CRUD |
| intelligence | `blueprints/intelligence.py` | Existing analysis |
| career_intel | `blueprints/career_intel.py` | Career intelligence (NEW) |
| resumes | `blueprints/resumes.py` | Resume/cover generation |
| rules | `blueprints/rules.py` | Scoring config |

| Service | File | Purpose |
|---------|------|---------|
| worker | `services/worker.py` | Job processing pipeline |
| company_worker | `services/company_worker.py` | Company processing |
| career_intel | `services/career_intel.py` | Career intelligence (concurrency-locked) |

## Frontend

**Pages**: JobsPage, CompaniesPage, ResumeTab, CareerIntelTab, IntelligenceTab, RulesTab
**Hooks**: useJobs, usePending, useCompanies, useIntelligence, useCareerIntel, useResume, useWorkflow

## Data Flows

### Job Processing
URL → pending_jobs → Fetch → Extract Raw → Extract Structured → Analyze & Score → Summary → Save to DB → WebSocket streams to frontend

### Career Intelligence (concurrency-locked, one at a time)
User clicks Generate → Lock acquired → Collect data (jobs, companies, skills, preferences) → Mimo CLI generates JSON → Save each section to career_insights → Lock released → Frontend polls progress

### Scoring
Job + Company data → SHARED rules → JOB rules → COMPANY_PRODUCT rules → COMPANY_RECRUITING rules → fit_score (weighted avg) + success_score (weighted avg) → overall_score = fit × 0.6 + success × 0.4

## Key Patterns
1. Blueprint architecture per feature
2. Prompt templates as `.txt` files with `{variable}` interpolation
3. Background threading for long operations
4. WebSocket for real-time processing, SSE for queue status
5. Concurrency lock for career intelligence (single-run enforcement)
