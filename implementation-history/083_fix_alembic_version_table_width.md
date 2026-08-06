# Prompt 083 - Fix Alembic Version Table Width + CI Test Report Guard

## Objective

CI fails on the backend job with two chained errors:

1. `sqlalchemy.exc.DataError: (psycopg.errors.StringDataRightTruncation) value
   too long for type character varying(32)` when alembic tries to stamp
   `company_003_add_companies_raw_content` (37 chars) into
   `alembic_version.version_num`, which Alembic 1.18.5 creates as `VARCHAR(32)`.
   Also over 32 chars: `company_005_add_parent_company_id` (33) and
   `company_006_normalize_intelligence_score_keys` (45). Local DB only worked
   because its column had been widened to `varchar(64)` by hand (never captured
   in a migration/script).
2. `dorny/test-reporter@v1` "No test report files were found" — a cascade: the
   migration step failed first, so pytest never ran and no `test-results/pytest.xml`
   was produced; the `if: always()` report step then hard-errors because the
   glob matched nothing (`fail-on-error: false` does not cover missing files).

## Implementation Steps

1. `apps/alembic/env.py`: add `ensure_widened_version_table(connection)` which,
   before `context.run_migrations()`, either `ALTER TABLE alembic_version
   ALTER COLUMN version_num TYPE VARCHAR(255)` (table exists) or `CREATE TABLE
   alembic_version (version_num VARCHAR(255) NOT NULL)` (fresh DB). Alembic
   reuses the pre-created table via `checkfirst=True`. Idempotent.
2. `.github/workflows/ci.yml`: guard `Publish backend test report` with
   `if: always() && hashFiles('test-results/pytest.xml') != ''`.

## Verification

- `DATABASE_URL=...:55432 uv run alembic upgrade head` against a throwaway
  fresh Postgres: reaches `company_006_normalize_intelligence_score_keys`,
  column becomes `VARCHAR(255)`.
- `alembic current` against the existing local DB: still `(head)` — idempotent
  ALTER path safe.
- Backend tests: 1221 passed.

## Constraints

- Fix → SemVer PATCH bump to **3.4.2** in all version locations +
  `check-version.sh`.
