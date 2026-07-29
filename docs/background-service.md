# Background Service

The background service is an independent ARQ worker runtime for executing long-running AI workflows.

## Architecture

```
HTTP API (FastAPI)    Background Worker (ARQ)
       |                      |
       | enqueue via Redis    | dequeue from Redis
       v                      v
    Redis Queue ────────────> ARQ Worker
                                  |
                                  v
                           Application Services
                                  |
                                  v
                             Domain Logic
                                  |
                                  v
                             Database
```

## Components

- **app/background/** — Background worker application
- **Redis** — Queue backend for ARQ
- **ARQ** — Async job queue framework

## Worker Types

- `process_job` — Job processing workflow
- `process_company` — Company analysis workflow
- `process_generation` — Resume/cover letter generation

## Running

```bash
# Start background worker standalone
python -m background.main

# Start with backend + frontend
python app/start.py dev --background

# Docker Compose
docker compose up -d
```
