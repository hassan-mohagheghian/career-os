# Prompt 067 - Remove `SQLAlchemyPendingJobRepository` → Consolidate into `SQLAlchemyJobRepository`

## Objective

Remove `sa_pending_job_repository.py` and move all job-related repository methods into
`sa_job_repository.py`. Two parallel implementations querying the same `JobModel` table
is redundant. All job mutations should go through one class.

## Current State

`SQLAlchemyPendingJobRepository` has 24 methods, most of which duplicate
`SQLAlchemyJobRepository`. Consumers: CLI, websocket router, stream server,
generation repository, DI provider, and 7 test files.

## Implementation Steps

### 1. Add missing methods to `sa_job_repository.py`

Move these from the pending repo (drop the unused `version` param from `reset_steps`):

- `get_max_queue_order()`
- `mark_processing_as_waiting()`
- `reset_processing_orphans()`
- `get_queued_items()`
- `reset_steps(item_id)` (no version param)
- `get_all_for_stream()`
- `create_pending_job()` → merge into `create_job()` as a pass-through

### 2. Update `entrypoints/cli.py`

- Remove `_get_pending_repo()` function
- Replace all `_get_pending_repo()` calls with `_get_job_repo()`
- Adapt method calls: `list_pending()` → `list_jobs()` or similar

### 3. Update `dependencies.py`

- Remove `get_pending_repo()` (already DEPRECATED)

### 4. Update `websocket_router.py`

- `SQLAlchemyPendingJobRepository` → `SQLAlchemyJobRepository`
- `repo.reset_steps(int(job_id), version=2)` → `repo.reset_steps(int(job_id))`

### 5. Update `stream_server.py`

- Replace all 7 `SQLAlchemyPendingJobRepository` import sites with `SQLAlchemyJobRepository`

### 6. Update `generation_repository.py`

- Replace import with `SQLAlchemyJobRepository`

### 7. Delete `sa_pending_job_repository.py`

### 8. Update tests

- Delete `test_pending_repository.py` and `test_sa_pending_job_repository_extra.py`
- Remove `TestSAPendingJobRepository` from `test_sa_repositories.py`
- Update `test_stream_server.py` imports
- Update `test_cli.py` patches (`_get_pending_repo` → `_get_job_repo`)
- Remove `get_pending_repo` DI overrides from conftest files

## Testing Requirements

Run: `uv run pytest apps/backend/tests/ -v`

## Constraints

- All existing tests must pass.
- `shared/domain/repositories/pending_repository.py` stays (used by company pending repo).
- `companies/presentation/api/pending_router.py` is unchanged.
