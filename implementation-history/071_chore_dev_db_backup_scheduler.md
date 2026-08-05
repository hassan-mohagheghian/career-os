# Prompt 071 - Dev DB Backup Scheduler

## Objective

Restore the background scheduler for `./start dev` (the previous cleanup task
was removed), repurposed as a database backup task: during dev, dump the main
PostgreSQL DB every N minutes and keep only the N most recent backups.

Also fixes the original "task not found" warning by registering the scheduled
task in `shared.infrastructure.taskiq.tasks`, which is part of the worker's
`TASK_MODULES`.

## Current State

- The scheduler was removed entirely (see 069).
- `pg_dump` is not installed on the host; PostgreSQL runs in Docker
  (`job-search-postgres-1`), so backups use `docker exec ... pg_dump`.
- `backups/` already exists (untracked) and is now gitignored.

## Implementation Steps

1. Config in `apps/backend/shared/infrastructure/config/app_config.py` + `.env`:
   - `DB_BACKUP_INTERVAL_MINUTES` (default 10)
   - `DB_BACKUP_KEEP_COUNT` (default 3)
   - `DB_BACKUP_DIR` (default `<repo>/backups`, resolved to absolute)
   - `DB_BACKUP_CONTAINER` (default `job-search-postgres-1`)
2. New `apps/backend/shared/infrastructure/database/backup_service.py`:
   - `create_db_backup()` — runs `docker exec <container> pg_dump -U <user>
     -d <db> --format=custom --no-owner`, streams stdout to
     `jobsearch_YYYYMMDD_HHMMSS.dump`, deletes partial file on failure.
   - `list_backups()` / `prune_old_backups(keep)` — retention pruning.
   - `run_db_backup()` — create + prune, returns summary dict.
3. New task `periodic_db_backup` in `shared.infrastructure.taskiq.tasks` with
   `schedule=[{"interval": minutes*60}]`.
4. Recreate `apps/backend/entrypoints/scheduler.py` (LabelScheduleSource).
5. Re-wire scheduler into `apps/start.py` (`PID_SCHED_FILE`, `_start_scheduler`,
   dev/background/stop/status wiring, banner + help text).
6. Docs: `docs/queue/processing/taskiq-processing.md` + `README.md`.

## Testing Requirements

- `apps/backend/tests/shared/infrastructure/database/test_backup_service.py`
  (create/prune/list/run with mocked subprocess + tmp dirs).
- Backend suite: `uv run pytest apps/backend/tests/ -v`.

## Constraints

- No API changes.
- Backups must be gitignored (`/backups/`).
