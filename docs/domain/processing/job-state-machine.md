# Job State Machine

## Status Enum

Defined in `app/server/shared/infrastructure/process/models.py` as `JobStatus`:

```python
class JobStatus(str, Enum):
    CREATED = 'created'
    QUEUED = 'queued'
    WAITING = 'waiting'
    STARTING = 'starting'
    FETCHING = 'fetching'
    ANALYZING = 'analyzing'
    GENERATING = 'generating'
    FINALIZING = 'finalizing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
```

## State Machine Properties

- **Deterministic**: Every status has a defined set of valid target states
- **Explicit**: No ambiguous boolean flags (e.g., no separate `is_processing` column)
- **Terminal states**: `completed`, `failed`, `cancelled` — once reached, no further processing occurs
- **Active states**: `starting`, `fetching`, `analyzing`, `generating`, `finalizing` — worker is actively processing

## Valid Transitions

| From       | To                                   |
| ---------- | ------------------------------------ |
| created    | queued, failed, cancelled            |
| queued     | waiting, created, failed, cancelled  |
| waiting    | starting, created, failed, cancelled |
| starting   | fetching, failed, cancelled          |
| fetching   | analyzing, failed, cancelled         |
| analyzing  | generating, failed, cancelled        |
| generating | finalizing, failed, cancelled        |
| finalizing | completed, failed, cancelled         |
| completed  | queued, cancelled                    |
| failed     | queued, cancelled                    |
| cancelled  | created, queued                      |

## Enforcement

Transitions are enforced at two levels:

1. **Repository level**: `SQLAlchemyPendingRepository.update_status()` calls `_validate_transition()` which checks `VALID_TRANSITIONS` dict
2. **Queue manager level**: Before any status change, `_validate_transition()` checks the transition is valid

## Legacy Compatibility

The `ItemStatus` enum is preserved for backward compatibility during migration:

```python
ItemStatus.PENDING    → JobStatus.CREATED
ItemStatus.QUEUED     → JobStatus.QUEUED
ItemStatus.PROCESSING → JobStatus.FETCHING
ItemStatus.PAUSED     → JobStatus.WAITING
ItemStatus.DONE       → JobStatus.COMPLETED
ItemStatus.FAILED     → JobStatus.FAILED
```

## Database Model

The `pending_jobs` table stores:

- `status` — current job status (JobStatus string value)
- `previous_status` — previous status (for rollback/audit)
- `current_node` — current LangGraph node name
- `retry_count` — number of retries attempted
- `failure_details` — structured error information (JSON)
- `auto_process` — whether to auto-enqueue on creation (boolean int)
