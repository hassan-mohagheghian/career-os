# AI Agent Instructions

## Project Structure

```
app/
├── ai/                 AI Agent Orchestration Layer
│   ├── providers/      LLM provider abstraction (mimo, openai, local)
│   ├── agents/         Agent implementations + LangGraph workflows
│   ├── tools/          Domain tools wrapping existing services
│   └── prompts/        Centralized prompt registry
├── server/          Python Flask backend
│   ├── app.py       Entry point — do NOT add routes here
│   ├── blueprints/  API routes (add new routes here)
│   ├── services/    Business logic
│   ├── core/        DB schema, queue
│   └── prompts/     AI prompt templates
└── client/
    └── src/
        ├── features/    Feature-based (each has components/, hooks/)
        ├── shared/      Shared UI, hooks, lib
        └── layout/      Header, Sidebar
```

## Coding Rules

### Backend
- Add new API routes in `blueprints/` — one file per domain
- Use `get_db()` for database connections (always close after use)
- Background tasks use `threading.Thread(target=..., daemon=True)`
- **New code must use AI provider abstraction** — agents never call MimoRunner directly
- Structured logging: `from services.process.logging_config import get_logger`
- Follow OOP, SOLID, DDD, TDD, Design Patterns for all Python code

### Frontend
- Feature components go in `features/{name}/components/`
- Feature hooks go in `features/{name}/hooks/`
- Shared components in `shared/components/`
- shadcn/ui primitives in `shared/ui/`
- All files must be `.ts` or `.tsx` — no JavaScript

### Patterns to Follow
- Flask Blueprints for API routes
- Feature-based frontend architecture
- WebSocket for real-time updates (not polling)
- Concurrency lock for AI generation (only one at a time)
- Version column for retry tracking
- **LLMProvider abstraction** for all AI calls (not direct MimoRunner)
- **Agent → Tool → Service** layering (agents orchestrate, tools wrap services)
- **LangGraph workflows** for multi-step AI pipelines

### Patterns to Avoid
- Do NOT use ORM — raw SQL only
- Do NOT add routes in `app.py`
- Do NOT use `print()` — use `structlog`
- Do NOT create new UI component libraries — use shadcn/ui
- Do NOT add paid API dependencies

## Change Guidelines

Before modifying code:
1. Understand the affected module and its neighbors
2. Check existing patterns in similar files
3. Preserve architecture boundaries (features don't cross-import)
4. Add or update tests for any changed behavior
5. Run `python -m pytest tests/` and `npx vitest run`

## Agent Workflow

1. **Read** `docs/CONTEXT.md` for project understanding
2. **Explore** the specific files you need to modify
3. **Plan** the changes before implementing
4. **Implement** with minimal, focused changes
5. **Test** — run the relevant test suite
6. **Verify** — ensure build passes
