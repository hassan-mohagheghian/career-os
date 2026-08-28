# Prompt 193 - Fix: processing_001 migration uses unavailable PGInspector.has_column

## Objective

CI `uv run alembic upgrade head` failed on a fresh database with:

    File ".../apps/alembic/processing/versions/processing_001_add_heartbeat_at.py", line 28, in upgrade
        if not insp.has_column("processing_executions", "heartbeat_at", schema="processing"):
               ^^^^^^^^^^^^^^^
    AttributeError: 'PGInspector' object has no attribute 'has_column'. Did you mean: 'get_columns'?

Make the processing_001 migration idempotent guard compatible with the
installed SQLAlchemy / PGInspector.

## Root Cause

#191 added an idempotency guard to `processing_001` that called
`inspect(bind).has_column(...)`. The `PGInspector` subclass in this project's
SQLAlchemy version does **not** implement `has_column` (only `has_table` and
`get_columns`), so the migration raised `AttributeError` on a fresh DB.

## Implementation Steps

1. Rewrite the `has_column` check in `processing_001` `upgrade()`/`downgrade()`
   to check column presence via `inspect(bind).get_columns(...)` and compare
   names (after a `has_table` guard), instead of the unsupported `has_column`.
2. Validate on a **fresh** database (exact CI path):
   create an empty Postgres DB, run `DATABASE_URL=<fresh> uv run alembic upgrade
   head`, confirm `processing.processing_executions` ends up with
   `heartbeat_at`. Then drop the test DB. (Reproduced locally and passed.)
3. Update `AGENTS.md` rule 14 schema-creation bullet to specify the safe guard
   pattern (`has_table` + `get_columns`, not `has_column`).

## Files Modified / Created

- Edited: `apps/alembic/processing/versions/processing_001_add_heartbeat_at.py`
- Edited: `AGENTS.md` (rule 14 — idempotency guard pattern)
- Created: `implementation-history/193_fix_processing_migration_has_column.md`

## Testing Requirements

- `uv run alembic upgrade head` on a fresh DB succeeds (verified locally against
  a throwaway Postgres database).
- `processing.processing_executions` contains `heartbeat_at` after upgrade.

## Constraints

- No behavior change to the migration's end state.
- Guard must work on both fresh and pre-populated DBs.
