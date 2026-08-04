# Prompt 065 - Job Repository Auto-Bumps `updated_at`

## Objective

Make job mutations bump the job's `updated_at` timestamp consistently so the
field reflects the last time the job changed — including processing writes.

`updated_at` is the default sort for the Jobs List (`list_jobs_v2` /
`search_jobs` / `search_jobs_cursor`). Today the value is stale after several
job mutations, and the two repository implementations disagree.

## Current State

In `apps/backend/jobs/infrastructure/repositories/sa_job_repository.py`:

- `update_fields` (bulk `update()`) does **not** touch `updated_at`.
- `update_status` (bulk `update()`) does **not** touch `updated_at`.
- `pick_queued_item` (ORM instance write) sets `status = 'processing'` but does
  **not** touch `updated_at`.

By contrast, the legacy `PendingJobRepository` (`shared/infrastructure/process/
repository.py`) and `SQLAlchemyPendingJobRepository.pick_queued_item`
(`sa_pending_job_repository.py:162`) always stamp `updated_at`.

Processing writes that currently do **not** bump the timestamp:

- `JobService.persist_prepared_context` → `update_fields(raw_description=…, description=…)`
  (context preparation phase).
- The `status = 'processing'` transition in `pick_queued_item`.
- Any failure/retry status write through `update_status`.

The analysis persist node (`persist_node.py:82`) already passes `updated_at`
explicitly, so a successful full process bumps it — but only when at least one
field or score is written, and the surrounding lifecycle writes are not stamped.

## Implementation Steps

### 1. Auto-bump in `sa_job_repository.py`

Stamp `updated_at` automatically, while allowing callers to override it:

- `update_fields`: `fields.setdefault("updated_at", _now_iso())` before the
  bulk update.
- `update_status`: `extra.setdefault("updated_at", _now_iso())` when building
  the update dict.
- `pick_queued_item`: set `model.updated_at = _now_iso()` alongside
  `model.status = 'processing'`.

Use `datetime.now(UTC).isoformat()` (ISO string) to match the Text column and
the value format used by `shared/infrastructure/config/queue.py`.

Explicitly-passed `updated_at` values keep winning (callers in `queue.py`,
`persist_node.py` already pass their own `now`).

### 2. Leave `persist_node.py` untouched

It passes `updated_at` explicitly — harmless redundancy with `setdefault`.

## Testing Requirements

Backend tests in `tests/jobs/infrastructure/repositories/test_sa_job_repository_extra.py`:

- `update_fields` bumps `updated_at` to now (was a fixed old value).
- `update_fields` honours an explicitly-passed `updated_at`.
- `update_status` bumps `updated_at`.
- `pick_queued_item` bumps `updated_at` on the picked row.

Run: `uv run pytest apps/backend/tests/jobs/infrastructure/repositories/ -v`.

## Important Constraints

- Only `sa_job_repository.py` changes behavior; do not touch
  `sa_pending_job_repository.py`, the legacy `PendingJobRepository`, or any
  API contracts.
- `persist_node.py` and `JobService.persist_prepared_context` need no changes.
- All existing repository tests must keep passing.
