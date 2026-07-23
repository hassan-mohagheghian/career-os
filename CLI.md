# Job Search App — CLI Reference

## Quick Start

```bash
# Start everything (backend + frontend)
./start.sh

# Or start individually
./start.sh backend    # Flask server on :5000
./start.sh frontend   # Vite dev server on :5173
```

## Commands

| Command | Description |
|---------|-------------|
| `./start.sh` | Start backend + frontend, wait for Ctrl+C |
| `./start.sh backend` | Start only the Flask backend |
| `./start.sh frontend` | Start only the Vite frontend |
| `./start.sh stop` | Stop all running processes |
| `./start.sh status` | Show status of all processes |

## Process Management

### Graceful Shutdown

The app handles shutdown gracefully:

- **SIGTERM/SIGINT** (Ctrl+C): Terminates all background mimo processes, marks active jobs as cancelled in DB
- **atexit handler**: Backup cleanup if signal handlers don't fire
- **Process tracking**: All subprocesses are registered and cleaned up on exit

### Killing Stuck Processes

```bash
# Stop everything cleanly
./start.sh stop

# Or kill mimo processes manually
pkill -f "mimo run"

# Check what's running
./start.sh status
```

## Architecture

### Backend (Python/Flask)
- Entry: `app/server/app.py`
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
| `FLASK_DEBUG` | `1` | Enable Flask debug mode |

## Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :5000
lsof -i :5173

# Kill existing processes
./start.sh stop
```

### Mimo processes stuck
```bash
# Check running mimo processes
./start.sh status

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
