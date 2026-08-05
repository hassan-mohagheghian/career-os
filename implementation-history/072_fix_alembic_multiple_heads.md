# Prompt 072 - Fix Alembic Multiple Head Revisions

## Objective

Fix the CI failure `Multiple head revisions are present for given argument
'head'` when running `uv run alembic upgrade head`, and confirm the `./start`
tool applies all migrations on every run.

## Current State

`apps/alembic/job/versions/` contained two diverging heads from the same
ancestor `42c200d12fd5`:

- `026_consolidate_job_type_fields` (consolidate job type fields)
- `job_003_add_job_favorite` (add favorite column to jobs)

So `alembic upgrade head` could not resolve a single target head. The local DB
had already been stamped at a (lost) merge head `job_004_merge_job_heads`, whose
migration file no longer existed.

## Implementation Steps

1. Recreate the merge migration joining both heads:
   `alembic merge -m "merge job favorites and job type fields heads"
   --rev-id job_004_merge_job_heads 026_consolidate_job_type_fields
   job_003_add_job_favorite`
   → `apps/alembic/job/versions/job_004_merge_job_heads_merge_job_favorites_and_job_type_fields_.py`
2. Verify:
   - `alembic heads` → single head `job_004_merge_job_heads`.
   - `alembic upgrade head` exits 0.
   - A throwaway DB migrates the full chain cleanly through the merge.
3. Confirm the `./start` tool already runs all migrations:
   - `_run_migrations()` runs `alembic upgrade head` in the `dev` and
     `backend` commands; `migrate` and `db up` commands also run it.
4. Docs: `docs/database/alembic-guide.md` — add a "Merge divergent migration
   heads" section.

## Testing Requirements

- `uv run alembic heads` shows exactly one head.
- `uv run alembic upgrade head` succeeds (exit 0).
- Full migration chain applies cleanly on a fresh database.
- `./start` (dev) applies migrations on boot.

## Constraints

- Do not delete the legacy flat migrations in `apps/alembic/versions/` (not in
  `version_locations`, ignored by alembic).
