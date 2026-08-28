# Prompt 192 - Fix: restore single Alembic head after processing branch

## Objective

CI command `uv run alembic upgrade head` (singular) failed with:

    ERROR Multiple head revisions are present for given argument 'head'; please
    specify a specific target revision, '<branchname>@head' ... or 'heads' for all heads

Also, local `uv run alembic upgrade heads` failed with
`relation "rules" already exists` / `CREATE TABLE shared.rules` because the dev
DB had all tables physically present but `alembic_version` was out of sync
(only `processing_001` stamped), so unapplied main-chain migrations tried to
recreate existing tables.

## Root Cause

- #191 introduced the `processing` context as an independent branch root
  (`023_add_processing_executions` with `down_revision = None`), which added a
  **second** head (`processing_001`) alongside the main head (`0a497bf191e2`).
- The repo (and CI) uses `alembic upgrade head` (singular), which requires a
  single head. A second head aborts the command.
- The local dev DB was out of sync: tables existed but migrations weren't
  stamped, so re-running upgrade attempted to recreate them.

## Implementation Steps

1. Create a merge migration combining the two heads into one:
   `uv run alembic merge -m "merge processing branch into main head"
   processing_001_add_heartbeat_at 0a497bf191e2` →
   `apps/alembic/processing/versions/47a6df55e081_merge_processing_branch_into_main_head.py`
   (`down_revision` is a tuple of both heads; no-op upgrade/downgrade).
2. Verify `uv run alembic heads` shows exactly one head (`47a6df55e081`).
3. Make the local dev DB consistent without recreating tables:
   `uv run alembic stamp head` (records current state; `upgrade head` then a
   no-op). This is a non-destructive one-time DB fix for an out-of-sync
   `alembic_version`.
4. Strengthen `AGENTS.md` rule 14 with a "Keep a single head" requirement: any
   change that introduces a second head must be merged with `alembic merge`
   before being merge-ready, so CI's singular `upgrade head` keeps working.

## Files Modified / Created

- Created: `apps/alembic/processing/versions/47a6df55e081_merge_processing_branch_into_main_head.py`
- Edited: `AGENTS.md` (rule 14 — single-head/merge requirement)
- Created: `implementation-history/192_fix_alembic_single_head.md`

## Testing Requirements

- `uv run alembic heads` → exactly one head.
- `uv run alembic history -r base:heads` → resolves with no missing parents.
- (CI) `uv run alembic upgrade head` on a fresh DB succeeds (single head).
- Local: `alembic upgrade head` is a no-op after `alembic stamp head`.

## Constraints

- Merge migration must be no-op (it only combines branch heads).
- Do not change migration behavior; only the revision graph.
- Follow the repo convention of a single merged head (see earlier
  `chore: merge alembic heads` commit).
