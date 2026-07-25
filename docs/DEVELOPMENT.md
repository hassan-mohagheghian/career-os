# Development Guide

## Prerequisites

- Python 3.14+
- Node.js 20+
- uv (Python package manager)
- Mimo CLI (`~/.mimocode/bin/mimo`)

## Local Setup

```bash
# Clone and start
git clone <repo-url>
cd job-search
./start.sh

# Or manually:
# Backend
cd app/server
uv sync
uv run python app.py  # Flask on :5000

# Frontend
cd app/client
npm install
npm run dev          # Vite on :5173
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AI_PROVIDER` | `mimo` | AI provider: `mimo`, `openai`, `local` |
| `DB_PATH` | `app/server/db/jobs.db` | SQLite database path |
| `TEMP_DIR` | `app/tmp` | Temporary files directory |
| `SECRET_KEY` | `dev-secret-key` | Flask secret key |
| `QUEUE_CONCURRENCY` | `2` | Max concurrent processing workers |

## Testing

```bash
# Backend (376 tests)
uv run pytest app/server/tests/ -v

# AI layer tests (70 tests)
uv run pytest tests/test_ai/ -v

# All tests
uv run pytest tests/test_ai/ app/server/tests/ -v

# Backend with coverage
uv run pytest app/server/tests/ --cov=services --cov=blueprints --cov=core --cov-report=term-missing

# Frontend (23 tests)
cd app/client && npx vitest run
```

## Code Style

### Python (Backend)
- Follow OOP, SOLID, DDD, TDD principles
- Use `structlog` for logging (no `print()`)
- Raw SQL via `get_db()` helper (no ORM)
- Flask Blueprints for API routes
- Background threading for long operations
- **AI calls via LLMService** — `from ai_compat import get_llm_service`

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

- **Backend logs**: `app/server/logs/` directory
- **Frontend**: Browser dev tools, Vite HMR
- **WebSocket**: SocketIO events visible in Network tab
- **Database**: `sqlite3 app/server/db/jobs.db` for direct queries
- **AI Provider**: Check `AI_PROVIDER` env var and `~/.mimocode/bin/mimo`
