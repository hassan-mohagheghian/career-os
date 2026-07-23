# Project Context

## Purpose

A full-stack application for intelligent job search, company analysis, resume generation, and career intelligence. It helps engineers find visa-sponsored roles by automating job discovery, analysis, and providing AI-driven insights.

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  React SPA  │────▶│  Flask API   │────▶│   SQLite    │
│  (Vite)     │     │  (port 5000) │     │  (jobs.db)  │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐
                    │  Mimo CLI    │
                    │ (AI engine)  │
                    └──────────────┘
```

## Core Modules

| Module | Location | Purpose |
|--------|----------|---------|
| Jobs | `blueprints/jobs.py`, `services/worker.py` | Job fetching, analysis, scoring |
| Companies | `blueprints/companies.py`, `services/company_worker.py` | Company research and analysis |
| Intelligence | `blueprints/intelligence.py` | Existing analysis (market, strategy, skills, networking) |
| Career Intel | `blueprints/career_intel.py`, `services/career_intel.py` | New career intelligence system |
| Resumes | `blueprints/resumes.py` | Resume/cover letter generation |
| Rules | `blueprints/rules.py` | Scoring rule configuration |
| Dashboard | `blueprints/dashboard.py` | Dashboard insights |

## Data Flow

1. User submits URL → `pending_jobs` table
2. Worker fetches content → extracts structured data
3. Mimo CLI analyzes → generates scores and insights
4. Results saved to `jobs`, `summaries`, `companies`
5. Intelligence analysis aggregates all data
6. Frontend displays via React components

## Key Design Decisions

- **Raw SQL over ORM**: Simpler, no migration framework needed, direct control
- **Mimo CLI as AI backend**: Subprocess-based, prompt templates in `.txt` files
- **Hash-based SPA routing**: No React Router dependency, simple tab switching
- **shadcn/ui**: Radix primitives with Tailwind styling, New York variant
- **SQLite**: Single file database, sufficient for single-user application
