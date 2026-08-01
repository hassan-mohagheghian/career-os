# ADR-018: Background Service with ARQ + Redis

## Status

Superseded

## Context

The project executes long-running AI workflows inside the FastAPI server process using a thread-based queue manager. This causes:

- Blocking server resources during AI execution
- No persistence of queue state across restarts
- Limited scalability
- No built-in retry mechanism
- Tight coupling between HTTP and processing logic

## Decision

Create a separate `app/background/` application using ARQ (async job queue) backed by Redis.

## Consequences

### Positive

- Server stays responsive during AI execution
- Queue state persists in Redis
- Workers can scale independently
- Built-in retry, timeout, and scheduling
- Clean separation of concerns

### Negative

- Additional infrastructure dependency (Redis)
- Slightly more complex local development setup
- Migration effort for existing queue/worker code

## Migration Strategy

1. Create `app/background/` package with ARQ workers
2. Create shared ARQ client module in server
3. Update routers to enqueue via ARQ instead of calling workers directly
4. Add Redis + background service to Docker Compose
5. Update CI/CD for Redis service
6. Keep backward-compatible queue adapter until all callers migrate
