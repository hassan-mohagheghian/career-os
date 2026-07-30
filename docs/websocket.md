Deprecated. Replaced by SSE.

# WebSocket Integration

## Architecture

Two WebSocket systems:

### 1. Socket.IO (Primary)

- Singleton connection via `socket.io-client`
- Automatic reconnection with exponential backoff
- Used for: job status, company status, skill roadmap, generation progress
- Event-driven: `on('job:update')`, `on('company:complete')`, etc.

### 2. Raw WebSocket (Workflow Terminal)

- Separate connection on port 8765
- Used exclusively for the workflow terminal UI
- JSON messages with types: `state`, `tool_output`, `step`, `complete`, `error`

## Room Management

Entity-level subscriptions:

- Jobs: `watchJob(id)` / `unwatchJob(id)`
- Companies: `watchCompany(id)` / `unwatchCompany(id)`
- Skills: `watchSkills()` / `unwatchSkills()`
- Generations: `watchGeneration(id)` / `unwatchGeneration(id)`

Rooms are automatically synced with visible data and cleaned up on unmount.

## Socket Reference

See `src/shared/hooks/useSocketIO.ts` for the full API.
