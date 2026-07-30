Deprecated. Replaced by SSE.

# WebSocket Event Protocol

## Transport

The system uses **Socket.IO** (via `python-socketio`) for real-time event delivery. The Socket.IO server is mounted as an ASGI app alongside FastAPI.

Connection: `socket.io(window.location.origin, { transports: ['polling', 'websocket'] })`

## Room Model

Events are scoped to **rooms**. A room is a named channel that clients join to receive events for a specific resource.

| Resource   | Room Pattern       | Example         |
| ---------- | ------------------ | --------------- |
| Job        | `pending_{pid}`    | `pending_42`    |
| Company    | `company_{cid}`    | `company_7`     |
| Generation | `generation_{gid}` | `generation_15` |
| Skills     | `skills`           | `skills`        |
| Insights   | `insights`         | `insights`      |

## Client → Server Events

### Room Management

```javascript
// Watch a job's events
socket.emit("watch_pending", { id: 42 });

// Unwatch a job
socket.emit("unwatch_pending", { id: 42 });

// Watch a company's events
socket.emit("watch_company", { id: 7 });

// Watch skill updates
socket.emit("watch_skills");

// Watch insight updates
socket.emit("watch_insights");
```

### Job Control

```javascript
// Cancel a job
socket.emit("cancel_job", { id: 42, table: "pending_jobs" });

// Reset a job (re-queue with cleared state)
socket.emit("reset_job", { id: 42, table: "pending_jobs" });
```

## Server → Client Events

### Job Events

All job events are prefixed with `pending:`.

#### `pending:update`

Emitted when a pipeline step changes.

```json
{
  "id": 42,
  "step": "fetch",
  "val": 0,
  "status": "fetching",
  "current_node": "fetch_url",
  "ts": "2026-07-29T10:30:00"
}
```

#### `pending:log`

Emitted when a workflow log entry is appended.

```json
{
  "id": 42,
  "step": "fetch",
  "msg": "Fetching https://example.com/job...",
  "ts": "10:30:00"
}
```

#### `pending:complete`

Emitted when processing finishes successfully.

```json
{
  "id": 42,
  "num": 123,
  "company": "Acme Corp",
  "ts": "2026-07-29T10:35:00"
}
```

#### `pending:error`

Emitted when processing fails.

```json
{
  "id": 42,
  "msg": "[fetch] Failed to fetch URL: Connection timeout",
  "step": "fetch",
  "ts": "2026-07-29T10:30:05"
}
```

#### `pending:progress`

Emitted during workflow execution with progress information.

```json
{
  "id": 42,
  "current_node": "extract_raw_content",
  "progress_pct": 42.9,
  "message": "Completed fetch_url (1523ms)",
  "completed_nodes": [
    "load_context",
    "validate_input",
    "fetch_url",
    "fallback_to_notes"
  ],
  "node_timings": {
    "load_context": 234.5,
    "validate_input": 12.3,
    "fetch_url": 1523.1,
    "fallback_to_notes": 1.2
  },
  "ts": "2026-07-29T10:30:10"
}
```

### Queue Events

#### `queue:status`

Emitted when queue state changes.

```json
{
  "processing": 2,
  "queued": 5,
  "pending": 3,
  "concurrency": 4
}
```

### Company Events

Prefixed with `company:`: `company:update`, `company:log`, `company:complete`, `company:error`.

### Generation Events

Prefixed with `generation:`: `generation:update`, `generation:log`, `generation:complete`, `generation:error`.

## Frontend Synchronization

On page load:

1. Fetch current pending list via `GET /api/pending`
2. Join Socket.IO room for each pending job
3. Listen for `pending:*` events
4. On reconnection, refetch and rejoin rooms

Browser refresh preserves state because:

- Status is stored in the database (backend source of truth)
- WebSocket reconnects and resumes listening
- Frontend refetches current state on load
