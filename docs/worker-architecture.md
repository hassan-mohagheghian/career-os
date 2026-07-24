# Worker Architecture

Processing pipeline for jobs and companies — queue, workers, real-time status.

## Overview

```
Frontend (React)
    │
    ├── REST API ──► Flask blueprints (pending.py, companies.py)
    │                    │
    │                    ▼
    │              Queue Manager (queue.py)
    │                    │
    │                    ├── Worker Thread 1 ──► process_job()
    │                    └── Worker Thread 2 ──► process_company()
    │
    └── SocketIO ──► Real-time updates (step, log, complete, error)
```

## Status Flow

```
pending → queued → processing → done
                         ├── failed
                         └── paused (via cancel)
```

## Key Components

### `services/process/` (DDD + SOLID)

| File | Responsibility | Pattern |
|------|---------------|---------|
| `models.py` | Domain entities, enums, events | Value Objects, Domain Events |
| `interfaces.py` | Abstract contracts (ABC) | Dependency Inversion |
| `repository.py` | SQLite persistence | Repository Pattern |
| `process_manager.py` | Subprocess lifecycle + process groups | Singleton |
| `temp_manager.py` | Temp file tracking + cleanup | Singleton |
| `mimo_runner.py` | mimo CLI invocation | Strategy |
| `broadcaster.py` | Real-time status delivery | Observer |
| `worker_base.py` | Pipeline skeleton | Template Method |
| `logging_config.py` | structlog configuration | — |

### `core/queue.py`

Queue manager — persistent, concurrent, survives restarts.

- **Concurrency**: configurable via `QUEUE_CONCURRENCY` env (default 2)
- **Atomic claiming**: `UPDATE ... WHERE status='queued'` prevents races
- **Orphan recovery**: on startup, resets stuck `processing` → `queued`
- **Graceful shutdown**: `stop(timeout=15)` joins workers, kills processes, cleans temp files
- **Cancel**: `cancel_job(id)` kills subprocess + sets `paused`
- **Reset**: `reset_job(id)` kills subprocess + clears steps + re-queues

## mimo Integration

mimo runs as a subprocess via `mimo run <prompt> --format json`.

| Flag | Purpose |
|------|---------|
| `--format json` | Streams JSON events to stdout (parsed for real-time status) |
| `--session <id>` | Continues a specific session (multi-step pipeline context) |
| `--continue` | Continues last session |
| `--dangerously-skip-permissions` | Auto-approves tool calls (always on in background) |

`MimoRunner` handles:
- Process group creation (`os.setsid()`) for clean cancellation
- JSON event parsing and broadcasting
- Session ID discovery from output
- Timeout enforcement

## Real-Time Updates

### Backend → Frontend (SocketIO)

Events are emitted per-room (`pending_{id}` or `company_{id}`):

| Event | Payload |
|-------|---------|
| `pending:update` | `{id, step, val, status, error, ts}` |
| `pending:log` | `{id, step, msg, ts}` |
| `pending:complete` | `{id, num, company, score, ts}` |
| `pending:error` | `{id, msg, step, ts}` |
| `company:update` | `{id, step, val, status, error, ts}` |
| `company:complete` | `{id, company_id, name, ts}` |
| `queue:status` | `{processing, queued, pending, concurrency}` |

### Frontend → Backend (SocketIO)

| Event | Payload | Effect |
|-------|---------|--------|
| `watch_pending` | `{id}` | Join room `pending_{id}` |
| `unwatch_pending` | `{id}` | Leave room |
| `watch_company` | `{id}` | Join room `company_{id}` |
| `cancel_job` | `{id, table}` | Kill subprocess, set paused |
| `reset_job` | `{id, table}` | Kill subprocess, clear steps, re-queue |

## Clean Shutdown

On SIGTERM/SIGINT/atexit:

1. `queue.stop(timeout=15)` — waits for workers, kills remaining processes
2. `ProcessManager.cleanup_all()` — kills orphaned subprocesses
3. `TempFileManager.cleanup_all()` — removes all temp files
4. Career intel runs cancelled
5. Skill roadmap jobs cancelled
6. `socketio.stop()` — stops WebSocket server
7. Processing items marked `paused` (not stuck in `processing`)

**Zero leaked resources**: no orphaned mimo processes, no temp files, no stuck DB states.

## Testing

Tests live in `app/server/tests/test_process/`. Run with:

```bash
uv run pytest app/server/tests/test_process/ -v
```

79 tests covering:
- Domain models (state transitions, value objects, events)
- ProcessManager (start, cancel, cleanup)
- TempFileManager (register, cleanup, cleanup_all)
- Broadcaster (SocketIO emit, listeners, fallback)
- WorkerBase (successful/failed/cancelled pipelines)
- Repository (CRUD, claim, counts)
- QueueManager (enqueue, cancel, reset, shutdown, orphans)
