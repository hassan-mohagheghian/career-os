# Development Guide

## Prerequisites

- Python 3.14+
- Node.js 20+
- uv (Python package manager)
- Mimo CLI (`~/.mimocode/bin/mimo`) — only required if `AI_PROVIDER=mimo`

## Local Setup

```bash
# Clone and start
git clone <repo-url>
cd job-search
./start

# Or manually:
# Backend
uv sync
uv run uvicorn app.server.entrypoints.api:fastapi_app --reload --port 5000

# Frontend
cd app/client
npm install
npm run dev          # Vite on :5173
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AI_PROVIDER` | `mimo` | AI provider: `mimo`, `openai`, `local`, `gemini` |
| `DB_PATH` | `app/server/db/jobs.db` | SQLite database path |
| `BACKEND_PORT` | `5000` | Backend server port |
| `FRONTEND_PORT` | `5173` | Frontend dev server port |
| `SECRET_KEY` | `dev-secret-key` | FastAPI secret key |
| `QUEUE_CONCURRENCY` | `2` | Max concurrent processing workers |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

## Testing

```bash
# Backend (376+ tests)
uv run pytest app/server/tests/ -v

# AI layer tests (70 tests)
uv run pytest tests/test_ai/ -v

# All tests
uv run pytest tests/test_ai/ app/server/tests/ -v

# Backend with coverage
uv run pytest app/server/tests/ --cov=jobs --cov=companies --cov=skills --cov=shared --cov-report=term-missing

# Frontend (23 tests)
cd app/client && npx vitest run
```

## Code Style

### Python (Backend)
- Follow OOP, SOLID, DDD, TDD principles
- Use `structlog` for logging (no `print()`)
- SQLAlchemy ORM for all database access (never raw SQL)
- FastAPI routers for API routes in bounded contexts
- Background threading for long operations
- **AI calls via LLMService** — `from shared.infrastructure.ai.compat import get_llm_service`

### TypeScript (Frontend)
- Feature-based architecture: `features/{name}/components/`, `features/{name}/hooks/`
- Shared code: `shared/{components,hooks,lib,ui}/`
- shadcn/ui components in `shared/ui/`
- Tailwind CSS with custom tokens (`text-3xs`, `text-2xs`)
- No `any` types where avoidable

### Naming Conventions
- Python: `snake_case` for functions/variables, `PascalCase` for classes
- TypeScript: `camelCase` for functions/variables, `PascalCase` for components/types
- Files: `snake_case.py` for Python, `PascalCase.tsx` for React components, `camelCase.ts` for hooks/utils

## Git Workflow

- Feature branches from `main`
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- All tests must pass before merge
- Run `uv run pytest tests/` and `npx vitest run` before committing

## Debugging

- **Backend logs**: `app/server/logs/` directory (structured JSON via structlog)
- **Frontend**: Browser dev tools, Vite HMR
- **WebSocket**: SocketIO events visible in Network tab (WS connection at `/ws`)
- **Database**: Use SQLAlchemy ORM models or Alembic for database operations. Never use raw SQL.
- **AI Provider**: Check `AI_PROVIDER` env var (`mimo`, `openai`, `local`, `gemini`)
