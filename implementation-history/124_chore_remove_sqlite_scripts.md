# Prompt 124 - Remove SQLite Migration Scripts

## Objective

Remove the now-obsolete SQLite migration/restore scripts. The platform has
fully migrated from SQLite to PostgreSQL — `app_config.py` requires a
PostgreSQL `DATABASE_URL`, the SQLAlchemy engine is PostgreSQL-only, tests run
against PostgreSQL, and CI uses a postgres service container. The one-time
SQLite→PostgreSQL data-migration scripts are no longer needed.

Scope of removal:
- `scripts/migrate_data.py` — SQLite→PostgreSQL migration (reads `app/server/db/jobs.db`)
- `scripts/migrate_sqlite_to_postgres.py` — SQLite→PostgreSQL migration
- `scripts/restore_from_sqlite.py` — restore SQLite backup into PostgreSQL

Current-facing docs are updated so no `sqlite`/`aiosqlite`/`jobs.db` reference
to the deleted scripts or to the old SQLite runtime remains.

---

# Current State

The project has fully moved to PostgreSQL:

- `shared/infrastructure/config/app_config.py` **requires** `DATABASE_URL`
  (raises `RuntimeError` if unset) and normalizes to the `psycopg` dialect.
- `shared/infrastructure/database/sqlalchemy_config.py` is PostgreSQL-only
  (schema-per-context `SCHEMAS`, `ensure_schemas()`, no SQLite branch).
- `apps/backend/tests/conftest.py` uses PostgreSQL exclusively (test DB
  derived from `DATABASE_URL` with a `_test` suffix).
- CI (`apps/backend/tests/`) runs against a postgres service container.

The three scripts in `scripts/` were used for the one-time data migration and
are now dead code. Several docs still describe the old SQLite-first runtime
(engine auto-detection, `schema_translate_map`, in-memory SQLite tests, SQLite
`DATABASE_URL` default, `aiosqlite`, SQLite connection notes) that no longer
matches the codebase.

---

# Implementation Steps

## 1. Delete the sqlite scripts

Delete (via `git rm`):
- `scripts/migrate_data.py`
- `scripts/migrate_sqlite_to_postgres.py`
- `scripts/restore_from_sqlite.py`

Keep `scripts/check-version.sh` (referenced by CI and AGENTS.md).

## 2. Update docs

Remove sqlite / aiosqlite / jobs.db references from current-facing docs
(historical records — `implementation-history/`, `CHANGELOG.md`, `docs/adr/` —
are left untouched):

- `docs/database/sqlalchemy-architecture.md` — engine auto-detect section,
  SQLite default `DATABASE_URL`, `schema_translate_map` description, SQLite
  testing section, "CI runs with both SQLite and PostgreSQL" claim.
- `docs/database/alembic-guide.md` — "SQLite-specific issues" troubleshooting
  section.
- `docs/architecture/backend-architecture.md` — "SQLite → PostgreSQL (future)"
  DB row, `aiosqlite` async note, `db_path`/`DB_PATH` env table, SQLite
  single-writer / connection notes.
- `docs/architecture/ARCHITECTURE.md` — SQLite DB diagram box + stack line.
- `docs/architecture/dependency-injection.md` — `sqlite:///` engine example.
- `docs/architecture/backend-structure.md` — `connection.py # SQLite
  connection management` comment.
- `docs/ai/checkpointing.md` — "For SQLite" section.
- `docs/testing/backend-testing.md` — `sqlite_master` query, `sqlite:///:memory:`
  fixtures, "in-memory SQLite" dependency note.
- `docs/testing/tdd-strategy.md` — in-memory SQLite fixture references.
- `docs/architecture/code-ownership-map.md` — `scripts/*.py` legacy shim row.
- `docs/architecture/folder-structure.md` and `docs/architecture/modular-monolith.md`
  — `scripts/` legacy-shim listing.

## 3. Docs trace

Write this implementation-history file and commit it with the change.

---

# Testing Requirements

Docs-only change; no backend/frontend tests are affected. Verification:

- `rg -n -i "sqlite|aiosqlite|jobs\.db" docs/` — no remaining stale
  current-facing references (historical dirs may retain them).
- Confirm no references to the 3 deleted scripts remain outside
  `implementation-history/` (and `CHANGELOG.md`/ADRs, which are historical).
- `git status` / `git diff` review.

---

# Important Constraints

- Do not modify app code: `jobs/application/commands/backfill_raw.py`,
  `backfill_structured.py`, `normalize_locations.py` and the SQLite checkpoint
  fallback in `ai/infrastructure/graphs/runtime/graph.py` still reference
  sqlite/`DB_PATH`; removing them is a separate, app-scope task.
- Do not modify `CHANGELOG.md`, `docs/adr/*`, or `implementation-history/*`
  (point-in-time records).
- No version bump unless a release is requested (AGENTS.md rule 12).
