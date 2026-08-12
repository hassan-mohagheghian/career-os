# Prompt 150 - Resolve Legacy application_preparation ExecutionType Crash

## Objective

Prompt 146 removed the `application_preparation` execution type (feature deleted:
Preparation repo/table dropped, `ExecutionType.APPLICATION_PREPARATION` removed from
`apps/backend/processing/domain/enums.py`). Databases that ran executions before the
removal still carry orphaned rows in `processing.processing_executions` with
`execution_type='application_preparation'`. Every repository read path
(`list_recent`, `list_by_target`, `active_execution`, `get_by_id`) calls
`ProcessingExecution.from_dict` (`apps/backend/processing/domain/entities/processing_execution.py:107`),
which does `ExecutionType(data["execution_type"])` and raises `ValueError` → the whole
API/snapshots 500. Fix both the data and the code so a legacy value can never crash a read.

## Current State

- `ExecutionType` (`apps/backend/processing/domain/enums.py`) has no
  `APPLICATION_PREPARATION`; the dev DB (`alembic_version == application_002`) still has
  `2 × (application_preparation, completed)` rows.
- `application_002_drop_preparation.py` (application chain, applied) dropped the
  `application_preparations` table but did **not** clean orphaned executions.
- `from_dict` is strict: `execution_type=ExecutionType(data["execution_type"])` (line 107).
- No `processing/versions` alembic dir (processing schema is not a per-context chain);
  the application chain owns the preparation feature removal.

## Changes

### 1. Data migration (ag.)
- New migration `application_003_cleanup_preparation_executions` in
  `apps/alembic/application/versions/`, generated via
  `ALEMBIC_TARGET_SCHEMA=application uv run alembic revision --autogenerate -m "<desc>"`
  (expected empty diff), then tuned `upgrade()`:
  `DELETE FROM processing.processing_executions WHERE execution_type = 'application_preparation'`,
  `downgrade()` no-op (irreversible). Parents chain from `application_002`.

### 2. Defensive legacy handling
- Add `ExecutionType.LEGACY = "legacy"` (docstring: type from a removed feature; never dispatched).
- `from_dict`: wrap the `ExecutionType(...)` cast in `try/except ValueError`; on failure use
  `ExecutionType.LEGACY`. Stored `status` is preserved (rows are `completed`/dead).

### 3. Docs (rule 13 + domain docs)
- `docs/domain/processing/processing-execution.md`: document the `LEGACY` fallback + the
  003 cleanup migration (legacy rows from removed features are hard-deleted).
- `docs/api/processing/get-processing-execution.md` + `get-processing-queue.md`: note that
  unknown/legacy execution types are mapped to `legacy` instead of 500.

## Testing Requirements

- `apps/backend/tests/processing/domain/test_execution.py`: add
  `test_from_dict_maps_unknown_execution_type_to_legacy` (data with
  `execution_type="application_preparation"` no longer raises; type is `LEGACY`, other
  fields intact) + `test_execution_type_legacy_value`.
- `apps/backend/tests/processing/infrastructure/repositories/test_sa_processing_execution_repository.py`:
  add a row with `execution_type="application_preparation"` in `_add_execution`-style helper
  and assert `list_recent` / `list_by_target` return it typed `LEGACY` (no ValueError).
- Migrations: `uv run alembic upgrade head`, then re-run and verify the orphaned rows are gone;
  downgrade one step (application_002) then re-upgrade works.
- Full: `uv run pytest apps/backend/tests/ -v`.

## Constraints

- Respect AGENTS.md rule 14 (autogenerate-first) and rule 15 (no cross-context FKs — the
  DELETE is a data migration touching `processing` schema, allowed).
- No `print()` (structlog); no raw SQL in app code (SQL lives only in the migration).
- Rule 8: legacy completion rows are dead metadata → hard delete.
- Single head must be preserved after the migration.