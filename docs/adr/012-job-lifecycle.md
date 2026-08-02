# ADR-012: Job Lifecycle Refactoring

## Status

Accepted (Sprint 12)

## Context

The Job processing pipeline had grown organically with:
- Multiple parallel processing paths (legacy worker + LangGraph worker)
- Two WebSocket systems (SocketIO + FastAPI WebSocket)
- Two broadcaster implementations
- Ambiguous statuses (6 states with boolean flags)
- Implicit state inference from step columns
- Hard-to-follow state transitions

## Decision

We redesigned the complete Job lifecycle with:

### 1. Explicit State Machine
- 11 explicit states replacing 6 ambiguous ones
- Valid transitions documented and enforced
- Terminal states: completed, failed, cancelled
- Active states: starting, fetching, analyzing, generating, finalizing

### 2. Single Source of Truth
- Status comes only from `pending_jobs.status`
- No inference from files, queue position, or frontend
- `previous_status` column for audit trail

### 3. LangGraph Owns Workflow State
- LangGraph state is the authority on execution progress
- No temporary/intermediate files
- Progress tracking through state `progress` dict
- Node-based status updates via mapping table

### 4. Unified Event System
- Domain events drive all WebSocket updates
- New events: JobCreated, JobQueued, JobStatusChanged, WorkflowNodeStarted, WorkflowNodeCompleted, WorkflowProgress
- Failure details structured: step, provider, exception, retry count, recoverable flag

### 5. FastAPI Only Orchestrates
- Endpoints validate, create, enqueue, return
- No inline processing
- Background workers do all heavy lifting

### 6. Frontend Auto-Synchronization
- WebSocket for real-time (no polling)
- HTTP fallback on initial load
- Auto-reconnect with room re-join
- Browser refresh preserves state

## Consequences

### Positive
- Deterministic lifecycle for every job
- Better observability (users see exact stage)
- Cleaner recovery on restart
- Easier debugging (explicit states + failure details)
- Frontend and backend always in sync
- No temp file leaks

### Negative
- Migration effort: existing pending_jobs records need status migration
- Frontend requires update to handle new status values
- More states mean more complex state machine logic

## Implementation Plan

1. ✅ Define new `JobStatus` enum with explicit states
2. ✅ Update `pending_jobs` model with new columns
3. ✅ Update queue manager transitions
4. ✅ Update repository methods
5. ✅ Add progress tracking to LangGraph workflow
6. ✅ Update `JobWorker` for dynamic status updates
7. [ ] Update frontend hooks for new status values
8. [ ] Update API endpoints for new statuses
9. [ ] Run integration tests
10. [ ] Deploy and monitor

## References

- [Job Lifecycle](../domain/processing/job-state-machine.md)
- [WebSocket Events](../websocket-events.md)
- [Workflow Progress](../workflow-progress.md)
- [Frontend Sync](../frontend-sync.md)
