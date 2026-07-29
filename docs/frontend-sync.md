# Frontend Synchronization

## Architecture

Frontend synchronization follows these principles:

1. **Backend is the single source of truth** — all status comes from `pending_jobs.status`
2. **WebSocket for real-time updates** — no polling
3. **HTTP fallback on page load** — initial state fetched via REST
4. **Auto-reconnect** — Socket.IO handles reconnection transparently

## Initial Load

On page load (`App.tsx` → `usePending` → `fetchPending()`):

```
1. GET /api/pending          → fetch all pending items
2. For each item:            → join Socket.IO room
   socket.emit('watch_pending', { id })
3. Register event listeners: → pending:update, pending:log,
                              pending:complete, pending:error
```

## Real-Time Updates

### Step Update (`pending:update`)
```
Backend: WorkerBase._mark_step() → Broadcaster.step_update() → SocketIO emit
Frontend: usePending handleUpdate → setPending(prev => prev.map(...))
```

Updates the pending item's step flags and status in local state.

### Log Entry (`pending:log`)
```
Backend: WorkerBase._log() → Broadcaster.log() → SocketIO emit
Frontend: usePending handleLog → setPending(prev => prev.map(...))
```

Appends log entry to the item's workflow_log array.

### Completion (`pending:complete`)
```
Backend: WorkerBase.process() → Broadcaster.complete() → SocketIO emit
Frontend: usePending handleComplete → sets status='completed'
```

Triggers a refresh of the processed jobs list.

### Error (`pending:error`)
```
Backend: WorkerBase.process() → Broadcaster.error() → SocketIO emit
Frontend: usePending handleError → sets status='failed', updates error field
```

## Browser Refresh Recovery

When a user refreshes the page:

```
1. React mounts → usePending initializes
2. fetchPending() called → GET /api/pending returns all items
3. New Socket.IO connection established
4. All watch_pending events re-emitted → rooms rejoined
5. Event listeners re-registered
6. State is correct because:
   - Status comes from database (persisted)
   - Processing continues in background (status was already updated)
   - WebSocket reconnects and resumes delivery
```

## State Management

The frontend uses React hooks (no Redux/Zustand):

- `usePending()` — manages the pending items array, WebSocket listeners, CRUD operations
- `useJobs()` — manages processed jobs list, filtering, sorting, pagination
- `useWorkflow()` — manages the workflow log terminal drawer

## Socket.IO Singleton

A single Socket.IO connection is shared across the app via `useSocketIO()` hook:
- Auto-reconnect with exponential backoff (1s → 5s max)
- Transport: polling with WebSocket upgrade
- Reconnection attempts: infinite

## Room Lifecycle

Rooms are managed in `usePending`:
- Items are tracked in `watchedRef` (Set of IDs)
- `syncWatchRooms()` ensures rooms match current data:
  - Leaves rooms for removed items
  - Joins rooms for new items
- Cleanup on unmount: leaves all watched rooms
