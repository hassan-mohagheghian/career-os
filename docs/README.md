# Documentation Index

This directory contains project documentation for both human developers and AI agents.

## Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| `architecture/ARCHITECTURE.md` | System design, entities, data flows, backend structure | Developers, AI agents |
| `CHANGELOG.md` | Version history with all changes | Everyone |
| `ROADMAP.md` | Completed features and future plans | Product managers, developers |

## For AI Agents

The following files are optimized for AI agent consumption:

- **`architecture/ARCHITECTURE.md`** — Complete system architecture with entity relationships, API endpoints, WebSocket events, data flows, and code organization. This is the primary reference for understanding the codebase.

- **`CHANGELOG.md`** — Structured changelog with categories (Added/Changed/Removed) for each version.

## For Developers

- **`architecture/ARCHITECTURE.md`** — Start here for system understanding
- **API docs at runtime**: `/api/docs/` (Swagger UI), `/api/redoc/` (ReDoc)
- **Root `README.md`** — Quick start, tech stack, navigation, features overview

## For Product Managers

- **`ROADMAP.md`** — Feature roadmap and completed work
- **`CHANGELOG.md`** — What shipped and when

## Architecture Overview

```
Frontend (React + TypeScript) → Flask API (Python) → SQLite DB → Mimo CLI (AI)
```

Key patterns:
- Feature-based frontend architecture (`features/`, `shared/`, `layout/`)
- Flask blueprints for API routes (10 blueprints)
- SQLite with raw SQL (no ORM)
- Mimo CLI subprocess for AI generation
- WebSocket for real-time updates
- Version tracking for retry/resume
