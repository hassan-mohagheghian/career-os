# Documentation Index

This directory contains project documentation for both human developers and AI agents.

## Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| `architecture/ARCHITECTURE.md` | System design, entities, data flows, backend structure | Developers, AI agents |
| `AI_ARCHITECTURE.md` | AI agent layer, providers, tools, workflow graphs | Developers, AI agents |
| `AI_AGENTS.md` | Coding rules, patterns, change guidelines | AI agents |
| `CHANGELOG.md` | Version history with all changes | Everyone |
| `CONTEXT.md` | Project overview, rules, boundaries | Everyone |
| `DEVELOPMENT.md` | Setup, testing, code style, debugging | Developers |
| `DOMAIN.md` | Domain knowledge, business rules, workflows | Everyone |
| `FEATURES.md` | Feature descriptions and status | Product managers, developers |
| `API.md` | REST API and WebSocket reference | Developers |
| `PROJECT_CONTEXT.md` | Full project context for AI agents | AI agents |

## Architecture Overview

```
Frontend (React + TypeScript) → Flask API (Python) → SQLite DB
                                    ↓
                            AI Agent Layer (LLMService)
                                    ↓
                            Provider Layer (Mimo / OpenAI / Local)
```

Key patterns:
- Feature-based frontend architecture (`features/`, `shared/`, `layout/`)
- Flask blueprints for API routes (10 blueprints)
- SQLite with raw SQL (no ORM)
- **LLMService** for all AI calls (provider abstraction)
- WebSocket for real-time updates
- Version tracking for retry/resume
- DDD, SOLID, TDD, Design Patterns
