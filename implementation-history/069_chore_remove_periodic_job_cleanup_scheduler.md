# Prompt 069 - Remove Periodic Job Cleanup Scheduler

## Objective

Remove the TaskIQ periodic scheduler and its `periodic_job_cleanup` task. It is
not needed during development: dev sessions run for short periods and the main
usage for now is job processing. The scheduled cleanup is also currently broken
— the worker does not import the scheduler module (so the task is never
resolvable) and the repository method it calls (`cleanup_stale_items`) does not
exist yet.

## Current State

- `apps/backend/entrypoints/scheduler.py` registers `periodic_job_cleanup` on a
  hourly cron via `LabelScheduleSource`.
- `apps/backend/entrypoints/worker.py` only imports
  `shared.infrastructure.taskiq.tasks`, so the worker logs
  `task "apps.backend.entrypoints.scheduler:periodic_job_cleanup" is not found`.
- `apps/start.py` starts the scheduler process (`taskiq scheduler
  apps.backend.entrypoints.scheduler:create_scheduler`) with its own PID file
  and stop/status wiring.

## Implementation Steps

1. Delete `apps/backend/entrypoints/scheduler.py`.
2. Remove scheduler wiring from `apps/start.py`:
   - `PID_SCHED_FILE` constant.
   - `_start_scheduler()` call in `_start_background()` and the `background` command.
   - `_start_scheduler()` function definition.
   - `_stop_service("scheduler", PID_SCHED_FILE)` calls (dev run, background command, `stop`).
   - Scheduler line in the `dev` banner and the `status` command.
   - Update `--background` help text to reference only the worker.
3. Update docs (`docs/queue/processing/taskiq-processing.md` Scheduling section,
   `README.md`) to note there is no periodic scheduler active for now.
4. Leave `cleanup_stale_items` for a future feature if reintroduced; it is
   currently unused.

## Testing Requirements

- Backend: `uv run pytest apps/backend/tests/ -v` passes.
- No behavior change to job processing: worker tasks (`process_company_task`,
  `process_generation_task`, `process_execution_task`) are untouched.
- `./start status` and `./start -b` no longer reference a scheduler.

## Constraints

- Do not touch `apps/backend/entrypoints/worker.py` task modules.
- Do not change any processing/queue API.
