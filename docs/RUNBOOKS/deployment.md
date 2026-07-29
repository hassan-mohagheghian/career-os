# Deployment Guide

## Local Development

```bash
./start
```

Opens FastAPI backend (port 5000) + React dev server (port 5173).

## Production Deployment

### Prerequisites
- Python 3.14+
- Node.js 20+
- Mimo CLI installed at `~/.mimocode/bin/mimo` (only if `AI_PROVIDER=mimo`)

### Steps

1. **Install dependencies**:
   ```bash
   uv sync
   cd app/client && npm ci && npm run build
   ```

2. **Build frontend**: The built files go to `app/client/dist/` and are served by FastAPI as static files.

3. **Start the server**:
   ```bash
   uv run uvicorn app.server.entrypoints.api:fastapi_app --host 0.0.0.0 --port 5000
   ```

4. **Verify**: Open `http://localhost:5000` — FastAPI serves the SPA.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_PATH` | No | `app/server/db/jobs.db` | SQLite database path |
| `AI_PROVIDER` | No | `mimo` | AI provider: `mimo`, `openai`, `local`, `gemini` |
| `BACKEND_PORT` | No | `5000` | Backend server port |
| `FRONTEND_PORT` | No | `5173` | Frontend dev server port |
| `SECRET_KEY` | No | `dev-secret-key` | FastAPI secret key |
| `QUEUE_CONCURRENCY` | No | `2` | Max concurrent workers |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins |

## Database

- SQLite file at `app/server/db/jobs.db` (configurable via `DB_PATH`)
- Schema managed via SQLAlchemy ORM + Alembic migrations
- Migrations run automatically on startup via `api.py` lifespan
- Backup: copy the `.db` file
