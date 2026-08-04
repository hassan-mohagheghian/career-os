# Agent Instructions

This file gives AI coding agents the context needed to work correctly in this repository.

## Project Overview

**Job Search Intelligence** is an AI-powered career platform for software engineers seeking visa-sponsored roles in Europe (Germany, Netherlands). It automates the job search workflow:

- Job discovery and processing (URL → fetch → extract → AI analysis → score → save)
- Company intelligence (profile extraction, visa assessment, Fit/Success/Overall scoring)
- Skills management (5-category taxonomy, aliases, AI roadmaps)
- Career insights (health score, market analysis, opportunity funnel)
- Resume and cover letter generation

## Quick Start

```bash
./start                                    # backend (5000) + frontend (5173)
uv run uvicorn apps.backend.entrypoints.api:fastapi_app --reload --port 5000
cd apps/frontend && npm run dev               # frontend dev server
```

## Tech Stack

| Layer    | Technology                                                             |
| -------- | ---------------------------------------------------------------------- |
| Backend  | Python 3.14, FastAPI, SQLAlchemy ORM + Alembic, Pydantic v2, structlog |
| Frontend | React, Next.js (App Router), TypeScript, shadcn/ui, Tailwind CSS       |
| AI       | LLMService + provider abstraction, LangGraph workflows                 |
| Queue    | TaskIQ + Redis background workers                                      |
| Realtime | SSE (`/api/sse/processing-events`)                                     |
| Testing  | pytest (backend), vitest (frontend)                                    |

## Repository Layout

```
app/
├── server/                    # Python FastAPI backend (DDD modular monolith)
│   ├── entrypoints/           # FastAPI app + SocketIO + CLI
│   ├── shared/                # Shared Kernel (domain, application, infrastructure)
│   ├── jobs/                  # Jobs bounded context
│   ├── companies/             # Companies bounded context
│   ├── skills/                # Skills bounded context
│   ├── rules/                 # Rules bounded context
│   ├── ai/                    # AI bounded context (LLM, LangGraph, providers)
│   ├── processing/            # Processing bounded context (executions, queue)
│   └── tests/                 # Test suite by bounded context
├── client/                    # Next.js frontend (FSD architecture)
│   └── src/
│       ├── app/               # App providers
│       ├── entities/          # Business entities
│       ├── features/          # Feature slices (jobs, companies, skills, ...)
│       ├── widgets/           # Page adapters, drawers
│       └── shared/            # API client, UI kit, hooks
├── alembic/                   # Database migrations
├── todo-prompts/              # Engineering task prompts for TODO generation (gitignored)
└── docs/                      # Full documentation
```

## Key Rules (Non-Negotiable)

1. All AI calls go through `LLMService` — never call providers directly.
2. Use SQLAlchemy ORM for all database access — never raw SQL.
3. All frontend code is TypeScript (`.ts` / `.tsx`) — no JavaScript.
4. Feature-based frontend: `entities/`, `features/`, `widgets/`, `shared/`.
5. Backend follows DDD modular monolith + hexagonal architecture.
6. Follow DDD / CQRS / OOP / SOLID / TDD / Clean Codes throughout.
7. Default sort is newest first (`created_at desc`).
8. Hard delete for processed jobs: delete the job and related tables.
9. All cards must have a delete button.
10. Do not add API routes in `entrypoints/api.py` — use per-context routers.
11. Do not use `print()` — use `structlog`.
12. Never change the version in only one place — keep all version references in sync (see `## Versioning` below).

## Versioning

The repo uses a **single SemVer number** (`MAJOR.MINOR.PATCH`). The `VERSION` file at the repo root is the machine source of truth; `CHANGELOG.md` is the human-facing release log.

Every release keeps these five locations identical:

- `VERSION` (source of truth)
- `CHANGELOG.md` — the **latest** `## [x.y.z]` header (bump = add a new entry at the top)
- `pyproject.toml` (`version`)
- `apps/frontend/package.json` (`version`)
- git tag `vX.Y.Z` (tagged on the release commit)

The backend reads the version from `VERSION` at runtime — FastAPI (`apps/backend/entrypoints/api.py`) and the CLI banner (`apps/start.py`) are synced automatically. `pyproject.toml` and `package.json` are static copies checked by script.

**To release:**

1. Bump SemVer based on the change: breaking → `MAJOR`, feature → `MINOR`, fix → `PATCH`.
2. Update `VERSION`, add the matching `## [X.Y.Z]` entry to the top of `CHANGELOG.md`, and update `pyproject.toml` + `apps/frontend/package.json`.
3. Run `./scripts/check-version.sh` — it must pass (exits non-zero on any mismatch).
4. Commit as `chore(release): vX.Y.Z`, then `git tag vX.Y.Z` and push the tag.

CI runs `./scripts/check-version.sh` on every push/PR, so a version touched in only one place fails the build.

## Testing

```bash
# Backend
uv run pytest apps/backend/tests/ -v

# Frontend
cd apps/frontend && npx vitest run

# All
uv run pytest apps/backend/tests/ -v && cd apps/frontend && npx vitest run

# With coverage (via the dev CLI)
./start test backend --coverage
./start test frontend --coverage
./start test all --coverage
```

## Development Workflow

Investigate → Update tests/docs → Code → Refine. Code, tests, and docs must never drift.

1. **Investigate (before coding)**
   - Read the relevant docs under `docs/` and the repo-root guides (`CONTEXT.md`, `DOMAIN.md`,
     `ARCHITECTURE.md`, `API.md`) for the affected module.
   - Read the existing tests for the module to learn conventions and expected behavior.
   - Understand the affected module and its neighbors; preserve architecture boundaries
     (contexts must not cross-import).
2. **Update tests + docs (before coding)**
   - Write or update the test(s) that describe the new behavior first (TDD red phase).
   - Update the affected docs (API, domain, architecture, UX) to reflect the planned
     behavior before implementing it.
3. **Code**
   - Implement the minimal, focused change to make the tests pass (TDD green phase).
   - Keep tests and docs in sync as you code — no drift between code, tests, and docs.
4. **Refine (after coding)**
   - Run the relevant test suite and fix failures.
   - Refactor for clarity, then run the checks for the changed layer:
     - Backend: `uv run pytest apps/backend/tests/ -v`
     - Frontend: `cd apps/frontend && npx vitest run` plus `npm run lint` and `npm run typecheck`
   - Re-read your change against the tests and docs and tighten anything inaccurate.

Rule: a change must not alter behavior without the corresponding test and doc updates.

## Documentation Entry Points

| File              | Purpose                                                          |
| ----------------- | ---------------------------------------------------------------- |
| `CONTEXT.md`      | Project context, target users, key rules                         |
| `DOMAIN.md`       | Core entities and business rules                                 |
| `ARCHITECTURE.md` | System design overview                                           |
| `API.md`          | API overview                                                     |
| `DESIGN.md`       | Product & UX design overview + wireframes                        |
| `docs/`           | Full documentation (ai/, api/, architecture/, domain/, ux/, ...) |
