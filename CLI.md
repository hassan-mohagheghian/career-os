# Job Search App — CLI Reference

## Quick Start

```bash
# Start everything (backend + frontend)
./start

# Or start individually
./start backend    # FastAPI server on :5000
./start frontend   # Vite dev server on :5173
```

## Commands

| Command | Description |
|---------|-------------|
| `./start` | Start backend + frontend, wait for Ctrl+C |
| `./start dev` | Start backend + frontend (same as default) |
| `./start backend` | Start only the FastAPI backend |
| `./start frontend` | Start only the Vite frontend |
| `./start stop` | Stop all running processes |
| `./start status` | Show status of all processes |
| `./start test` | Run all backend tests |
| `./start lint` | Run all linters |
| `./start format` | Run all formatters |
| `./start doctor` | Validate development environment |
| `./start migrate` | Run database migrations |
| `./start db up` | Run migrations up |
| `./start db down` | Rollback last migration |
| `./start db new NAME` | Create new migration |
| `./start docker up` | Start Docker containers |
| `./start docker down` | Stop Docker containers |
| `./start clean` | Remove build artifacts |
| `./start logs` | Stream logs |
| `./start version` | Show version |

## Port Configuration

Ports can be configured via `.env` or CLI flags:

```bash
# .env
BACKEND_PORT=5000
FRONTEND_PORT=5173

# CLI override
./start dev --backend-port 4000 --frontend-port 3000
./start backend --port 4000
./start frontend --port 3000
```

## Process Management

### Graceful Shutdown

The app handles shutdown gracefully:

- **SIGTERM/SIGINT** (Ctrl+C): Terminates all background mimo processes
- **Process tracking**: All subprocesses are registered and cleaned up on exit

### Killing Stuck Processes

```bash
# Stop everything cleanly
./start stop

# Or kill mimo processes manually
pkill -f "mimo run"

# Check what's running
./start status
```

## Architecture

### Backend (Python/FastAPI)
- Entry: `app/server/entrypoints/api.py`
- Port: 5000
- Database: SQLite at `app/server/db/jobs.db`
- Background workers: Threads for AI generation (career intel, skill roadmaps)

### Frontend (React/Vite)
- Entry: `app/client/src/main.jsx`
- Port: 5173 (dev)
- Build: `npm run build` → `app/client/dist/`

### AI Generation Pipeline
- Uses mimo CLI for AI-powered analysis
- Workers run in background threads
- Progress tracked in DB (`career_insight_runs`, `skill_roadmap_jobs`)
- Session IDs captured for external mimo interaction
- Processes registered for cleanup on shutdown

## API Endpoints (Key)

### Career Intelligence
- `GET /api/career-intelligence` — All sections
- `GET /api/career-intelligence/<section>` — Single section
- `POST /api/career-intelligence/refresh` — Generate all
- `POST /api/career-intelligence/<section>/refresh` — Generate section
- `GET /api/career-intelligence/progress` — Current progress
- `POST /api/career-intelligence/cancel` — Cancel running

### Skill Roadmaps
- `GET /api/skill-roadmaps?skill=<name>` — Get roadmap tree
- `POST /api/skill-roadmaps/generate` — Generate roadmap
- `POST /api/skill-roadmaps/extend` — Extend roadmap
- `POST /api/skill-roadmaps/finegrain` — Fine-grain roadmap
- `POST /api/skill-roadmaps/cancel?skill=<name>` — Cancel generation
- `GET /api/skill-roadmaps/progress?skill=<name>` — Get progress
- `PUT /api/skill-roadmap-progress/<id>` — Toggle topic completion
- `GET /api/skill-roadmap-progress/all` — All skills progress

### Tech Stack
- `GET /api/tech-stack` — List all skills
- `POST /api/tech-stack` — Add skill
- `PUT /api/tech-stack/<id>` — Update skill
- `DELETE /api/tech-stack/<id>` — Delete skill

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PATH` | `app/server/db/jobs.db` | SQLite database path |
| `TEMP_DIR` | `tmp` | Temporary files directory |
| `BACKEND_PORT` | `5000` | Backend server port |
| `FRONTEND_PORT` | `5173` | Frontend dev server port |

## Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :5000
lsof -i :5173

# Kill existing processes
./start stop
```

### Mimo processes stuck
```bash
# Check running mimo processes
./start status

# Force kill all mimo
pkill -9 -f "mimo run"

# Reset stuck jobs in DB
sqlite3 app/server/db/jobs.db "UPDATE skill_roadmap_jobs SET status='failed', error='Reset' WHERE status IN ('running','queued')"
```

### Database locked
```bash
# Check for WAL mode issues
sqlite3 app/server/db/jobs.db "PRAGMA journal_mode;"
# Should return 'wal'
```
