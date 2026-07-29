# Job Processing Architecture

## System Context

```
┌──────────┐     ┌──────────┐     ┌──────────────┐
│  Browser │◄───►│  FastAPI  │◄───►│  Queue Mgr   │
│ (React)  │     │ (REST +  │     │  (Thread)    │
│          │     │  SocketIO)│     │              │
└────┬─────┘     └────┬─────┘     └──────┬───────┘
     │                │                  │
     │ WebSocket      │ HTTP             │ picks items
     │ events          │                  │
     │                │                  ▼
     │                │         ┌──────────────┐
     │                │         │   Worker     │
     │                │         │ (process_job)│
     │                │         └──────┬───────┘
     │                │                │
     │                │                ▼
     │                │         ┌──────────────┐
     │                │         │  LangGraph   │
     │                │         │  Workflow    │
     │                │         └──────┬───────┘
     │                │                │
     │                │                ▼
     │                │         ┌──────────────┐
     │                │         │  Database    │
     │                │         │ (SQLite/PG)  │
     └────────────────┴─────────┴──────────────┘
```

## Layer Responsibilities

### FastAPI Layer
- HTTP endpoint for creating jobs (`POST /api/pending`)
- HTTP endpoint for listing jobs (`GET /api/pending`, `GET /api/jobs`)
- HTTP endpoint for job control (`POST /api/pending/{id}/process`, etc.)
- Socket.IO server for real-time events
- Validation and error handling
- Returns immediately after enqueuing — never processes inline

### Queue Manager
- Thread-based worker pool (configurable via `QUEUE_CONCURRENCY`)
- Persistence via SQLite/PostgreSQL
- Startup recovery of orphaned items
- Graceful shutdown with cleanup
- Enqueue/dequeue/cancel/reset operations

### Worker Layer
- `process_job(pid)` — entry point called by queue manager
- `JobWorker` — LangGraph-based implementation
- Updates pending_jobs status as nodes execute
- Emits progress events via broadcaster

### LangGraph Workflow
- 13-node directed acyclic graph
- Owns execution state (no temp files)
- Each node is a pure function: state → state
- Progress tracked in state `progress` dict
- Retry configured on extract/score nodes

### Database
- `pending_jobs` — queue items with status and progress
- `jobs` — processed job results
- `summaries` — job summaries
- Status is the single source of truth

### WebSocket
- Socket.IO for real-time event delivery
- Room-based subscriptions per job/company/generation
- Events: update, log, complete, error, progress
- Auto-reconnect on frontend

## Key Design Decisions

### Why not ARQ?
The current implementation uses a thread-based queue manager. The document mentions ARQ as a future goal, but the current infra uses threads for simplicity and to avoid Redis dependency.

### Why LangGraph?
LangGraph provides deterministic, observable, resumable workflow execution. The custom graph builder wraps both real LangGraph and a sequential fallback, providing flexibility.

### Why explicit states?
The 11 explicit states (vs the old 6) provide:
- Better observability (users see exactly what's happening)
- Deterministic recovery (knowing exact failure point)
- Finer-grained frontend progress
- Clearer failure attribution

## Event Flow

```
1. User submits URL via web UI
2. POST /api/pending → creates pending_jobs record (status=created)
3. If auto_process: POST /api/pending/{id}/process → enqueues
4. Queue manager picks item → status=starting
5. JobWorker._execute_pipeline() begins
6. For each LangGraph node:
   a. Update pending_jobs.status and current_node
   b. Execute node function
   c. Emit pending:progress via WebSocket
7. On success: status=completed, emit pending:complete
8. On failure: status=failed, emit pending:error
```
