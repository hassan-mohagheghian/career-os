# Deployment Guide

## Local Development

```bash
./start
```

Opens Flask API (port 5000) + React dev server (port 5173).

## Production Deployment

### Prerequisites
- Python 3.15+
- Node.js 20+
- Mimo CLI installed at `~/.mimocode/bin/mimo`

### Steps

1. **Install dependencies**:
   ```bash
   cd app/server && uv sync
   cd app/client && npm ci && npm run build
   ```

2. **Build frontend**: The built files go to `app/client/dist/` and are served by Flask.

3. **Start the server**:
   ```bash
   cd app/server && uv run python app.py
   ```

4. **Verify**: Open `http://localhost:5000` — Flask serves the SPA.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_PATH` | No | `app/server/db/jobs.db` | SQLite database path |

| `SECRET_KEY` | No | `dev-secret-key` | Flask secret key |
| `QUEUE_CONCURRENCY` | No | `2` | Max concurrent workers |

## Database

- SQLite file at `app/server/db/jobs.db`
- Schema auto-created on first run via `core/db.py`
- Migrations run automatically on startup via `migrations.py`
- Backup: copy the `.db` file
