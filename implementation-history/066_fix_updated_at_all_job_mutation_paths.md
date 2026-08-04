# Prompt 066 - Fix `updated_at` Not Bumping on All Job Mutation Paths

## Objective

Ensure every job mutation bumps `updated_at` consistently. Prompt 065 partially
fixed `update_fields`, `update_status`, and `pick_queued_item` in
`sa_job_repository.py`, but many other mutation paths still skip the timestamp.

## Current State

**Still broken in `sa_job_repository.py`:**

- `mark_deleted()` (line 168) — bulk `.update({"deleted": 1})`, no `updated_at`
- `mark_rescoring()` (line 172) — bulk `.update({"rescoring": ...})`, no `updated_at`
- `update_workflow_log()` (line 263) — bulk `.update({"workflow_log": ...})`, no `updated_at`
- `upsert()` (line 244) — ORM `setattr` loop, no `updated_at`
- `set_deleted_by_url()` (line 268) — bulk `.update({"deleted": 1})`, no `updated_at`

**Still broken in `sa_pending_job_repository.py`:**

- `update_status()` (line 63) — ORM setattr, no `updated_at`
- `update_fields()` (line 84) — ORM setattr, no `updated_at`
- `reset_steps()` (line 175) — bulk `.update(...)`, no `updated_at`
- `mark_processing_as_waiting()` (line 136) — bulk `.update(...)`, no `updated_at`
- `reset_processing_orphans()` (line 144) — bulk `.update(...)`, no `updated_at`

**Column definition (`job_model.py:51`):**

```python
updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
```

Only `default` (INSERT). No `onupdate`.

## Implementation Steps

### 1. `job_model.py` — add `onupdate`

```python
updated_at: Mapped[Optional[datetime]] = mapped_column(
    Text, default=datetime.utcnow, onupdate=datetime.utcnow
)
```

This covers all ORM instance writes (setattr + commit). Bulk `.update()` queries
still need explicit stamps.

### 2. `sa_job_repository.py` — stamp `updated_at` in remaining methods

For bulk `.update()` calls, add `"updated_at": datetime.now(UTC).isoformat()`:

- `mark_deleted`: add `updated_at` to the update dict
- `mark_rescoring`: add `updated_at` to the update dict
- `update_workflow_log`: add `updated_at` to the update dict
- `set_deleted_by_url`: add `updated_at` to the update dict

For the ORM-based `upsert()` update branch, set `updated_at` explicitly:

- `upsert`: `existing.updated_at = datetime.now(UTC).isoformat()` before commit

### 3. `sa_pending_job_repository.py` — stamp `updated_at` in remaining methods

For ORM setattr paths:

- `update_status`: add `m.updated_at = datetime.now(UTC).isoformat()`
- `update_fields`: add `m.updated_at = datetime.now(UTC).isoformat()`

For bulk `.update()` paths, add `"updated_at": datetime.now(UTC).isoformat()`:

- `reset_steps`: add to update dict
- `mark_processing_as_waiting`: add to update dict
- `reset_processing_orphans`: add to update dict

### 4. Leave alone

- `update_fields` in `sa_job_repository.py` — already has `setdefault`
- `update_status` in `sa_job_repository.py` — already has `setdefault`
- `pick_queued_item` in both repos — already stamps `updated_at`
- `persist_node.py` — passes `updated_at` explicitly, harmless redundancy
- Legacy `PendingJobRepository` — already stamps everywhere

## Testing Requirements

Backend tests:

- `test_sa_job_repository_extra.py`: add tests for `mark_deleted`, `mark_rescoring`,
  `update_workflow_log`, `upsert` (update branch), `set_deleted_by_url` all bumping
  `updated_at`.
- `test_sa_pending_job_repository_extra.py`: add tests for `update_status`,
  `update_fields`, `reset_steps`, `mark_processing_as_waiting`,
  `reset_processing_orphans` all bumping `updated_at`.

Run: `uv run pytest apps/backend/tests/jobs/infrastructure/repositories/ -v`

## Important Constraints

- Only repository infrastructure files change; no API contracts, no domain entities.
- `onupdate` covers ORM writes; bulk `.update()` queries still need explicit stamps.
- All existing tests must keep passing.
