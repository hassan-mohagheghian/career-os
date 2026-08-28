# Prompt 191 - Fix: processing migration schema does not exist on fresh DB

## Objective

CI (`uv run alembic upgrade head`) fails on a fresh database with:

    sqlalchemy.exc.ProgrammingError: (psycopg.errors.InvalidSchemaName)
    schema "processing" does not exist
    [SQL: ALTER TABLE processing.processing_executions ADD COLUMN heartbeat_at TEXT]

Make the processing context migrations apply cleanly on a fresh DB and prevent
regression.

## Root Cause

- `alembic.ini` `version_locations` lists only the per-context dirs
  (`apps/alembic/<ctx>/versions/`). The legacy single `apps/alembic/versions/`
  dir is NOT scanned.
- The processing schema + table creator (`023_add_processing_executions.py`)
  lived in the legacy, unscanned dir, so it never runs in CI → the `processing`
  schema is never created.
- `processing_001_add_heartbeat_at.py` then does
  `ALTER TABLE processing.processing_executions ...` against a missing schema.
- Additionally `processing_001`'s `down_revision` pointed at `0a497bf191e2`,
  which is a **job-branch** merge migration — an invalid cross-context link
  (also a violation of rule 14: hand-written migration).

## Implementation Steps

1. `git mv apps/alembic/versions/023_add_processing_executions.py
   apps/alembic/processing/versions/processing_000_initial.py` and rewrite it as
   a proper branch root (mirror `company_001`):
   - `revision = '023_add_processing_executions'` (keep id so already-applied
     dev DBs still recognize it)
   - `down_revision = None`
   - `branch_labels = ("processing",)`
   - `upgrade()`: `CREATE SCHEMA IF NOT EXISTS processing`, then create the table
     **only if it does not already exist** (inspect-based guard) so re-running
     on a DB that already has the table is safe.
2. Edit `apps/alembic/processing/versions/processing_001_add_heartbeat_at.py`:
   - `down_revision = '023_add_processing_executions'`
   - `upgrade()` prepends `op.execute("CREATE SCHEMA IF NOT EXISTS processing")`.
3. Validate the revision graph offline (no DB): `uv run alembic heads` (expect a
   single `processing` head) and `uv run alembic history -r base:heads`.

## Files to Modify / Create

- Move + rewrite: `apps/alembic/processing/versions/processing_000_initial.py`
  (was `apps/alembic/versions/023_add_processing_executions.py`)
- Edit: `apps/backend/.../processing_001_add_heartbeat_at.py`
- Edit: `AGENTS.md` rule 14 (add migration placement + schema-guard + graph
  verification rules)
- Create: `implementation-history/191_fix_processing_migration_schema.md`

## Testing Requirements

- `uv run alembic heads` resolves with one processing head.
- `uv run alembic history -r base:heads` shows no missing parents.
- (CI) `uv run alembic upgrade head` on a fresh DB succeeds — this is the exact
  failure that must not recur.

## Constraints

- Keep the existing revision id `023_add_processing_executions` to avoid
  breaking dev DBs that already stamped it.
- No cross-context `down_revision` links (rule 15: no FK/logical refs across
  schemas; migrations must be self-contained per schema).
- Follow the established `company_001` branch-root pattern.
