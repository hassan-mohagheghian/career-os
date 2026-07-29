# Documentation Index

This directory contains project documentation for both human developers and AI agents.

## Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| `architecture/ARCHITECTURE.md` | System design, DDD bounded contexts, entities, data flows | Developers, AI agents |
| `AI_ARCHITECTURE.md` | AI agent layer, provider abstraction, LangGraph workflows, tool system | Developers, AI agents |
| `AI_AGENTS.md` | Coding rules, patterns, change guidelines | AI agents |
| `CHANGELOG.md` | Version history with all changes | Everyone |
| `CONTEXT.md` | Project overview, rules, boundaries | Everyone |
| `DEVELOPMENT.md` | Setup, testing, code style, debugging | Developers |
| `DOMAIN.md` | Domain knowledge, business rules, workflows | Everyone |
| `FEATURES.md` | Feature descriptions and status | Product managers, developers |
| `API.md` | REST API and WebSocket reference | Developers |
| `PROJECT_CONTEXT.md` | Full project context for AI agents | AI agents |
| `websocket-events.md` | Socket.IO event protocol and room model | Developers |
| `workflow-progress.md` | LangGraph pipeline progress, 13-node state machine | Developers |
| `frontend-sync.md` | Frontend sync architecture (WebSocket + HTTP fallback) | Developers |
| `job-lifecycle.md` | 11-state job lifecycle, state transitions | Developers |
| `job-state-machine.md` | State machine enforcement, valid transitions table | Developers |

## Architecture Overview

```
Frontend (React + TypeScript) → FastAPI (Python) → SQLite DB (SQLAlchemy ORM)
                                    ↓
                         AI Agent Layer (LLMService + LangGraph)
                                    ↓
                      Provider Layer (Mimo / OpenAI / Local / Gemini)
```

Key patterns:
- Feature-based frontend architecture (`features/`, `shared/`, `layout/`)
- DDD modular monolith — 8 bounded contexts with layered architecture
- FastAPI routers per bounded context (domain → application → infrastructure → presentation)
- SQLite with SQLAlchemy ORM + Alembic migrations
- **LLMService** for all AI calls (provider abstraction with LangGraph workflows)
- WebSocket (python-socketio, ASGI mode) for real-time updates
- Version tracking for retry/resume
- DDD, SOLID, TDD, Design Patterns
