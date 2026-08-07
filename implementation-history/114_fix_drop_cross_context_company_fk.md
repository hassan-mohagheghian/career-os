# Prompt 114 - Fix: Drop Cross-Context Company FK on job_companies

## Objective

Fix a CI failure (`sqlalchemy.exc.ProgrammingError` / `psycopg.errors.DatatypeMismatch`)
when building a fresh database from the migration graph:

```
foreign key constraint "fk_job_companies_company_id_companies" cannot be implemented
DETAIL:  Key columns "company_id" and "id" are of incompatible types:
         character varying and integer.
```

The `job.job_companies.company_id` column is `VARCHAR(36)` but, at the moment the
constraint is created on a fresh database, `company.companies.id` is still
`INTEGER` — the company branch's `company_002_add_uuid_v7` migration (which
re-keys `companies.id` to `String(36)`) runs *after* `job_005_add_job_companies`
on the fresh graph.

Root cause: `job_005_add_job_companies` (and the ORM model `JobCompanyModel`)
declares a **cross-bounded-context foreign key** from the `job` schema to
`company.companies.id`. This violates AGENTS.md rule 15 (no FKs across bounded
contexts — cross-context links are logical references only). It happened to work
on the local dev DB because migrations were applied incrementally over time
(company_002 ran before job_005), but it breaks on any fresh build.

## Current State

- `apps/backend/jobs/infrastructure/models/job_company_model.py:35` declares
  `company_id: Mapped[str] = mapped_column(String(36), ForeignKey("company.companies.id", ondelete="CASCADE"), ...)`.
- `apps/alembic/job/versions/job_005_add_job_companies.py` creates the
  `fk_job_companies_company_id_companies` FK constraint.
- The local dev DB already applied `job_005` with the constraint present
  (verified via `pg_constraint`), so the fix needs both a corrected `job_005`
  (for fresh builds) and a follow-up migration that drops the constraint on
  databases that already applied it.
- Only cross-context FK in the codebase — all other `ForeignKey(...)` usages are
  within-context (audited via grep).

## Implementation Steps

1. **Model** (`job_company_model.py`): remove `ForeignKey("company.companies.id",
   ondelete="CASCADE")` from `company_id`; keep the plain `String(36)` column and
   its index (logical reference). Keep the within-context FK on `job_id` →
   `job.jobs.id` (supports rule 8 hard-delete cascade).
2. **Historical migration** (`job_005_add_job_companies.py`): remove the
   cross-context `sa.ForeignKeyConstraint(["company_id"], ["company.companies.id"])`.
   Keep the `job_id` FK, both indexes, and the `_table_exists` guard. This fixes
   fresh-database / CI builds.
3. **New migration** (autogenerate first, then tune): drop
   `fk_job_companies_company_id_companies` on databases where `job_005` already
   created it. Guard the `drop_constraint` so it is a no-op when the constraint
   does not exist (fresh databases).
4. **Verify** the migration graph: `uv run alembic history`, `uv run alembic heads`
   (single head), `uv run alembic upgrade head`, then downgrade/upgrade round-trip
   against the dev DB.
5. **Run backend tests**: `uv run pytest apps/backend/tests/ -v`.

## Testing Requirements

- `uv run alembic upgrade head` succeeds on the dev DB (constraint dropped).
- Fresh-database simulation: revert to a base state and re-upgrade (or verify the
  edited `job_005` no longer emits the cross-context FK).
- Full backend suite passes.

## Constraints

- AGENTS.md rule 15: no FKs across bounded contexts — never re-add a
  `ForeignKey` pointing into another context's schema. Referential integrity is
  enforced at the application/repository layer (existing `list_by_job`,
  `list_by_company`, `replace_for_job` already do this).
- AGENTS.md rule 14: generate the new migration with Alembic autogenerate FIRST,
  then tune content only.
- The `job_id` FK stays (within-context, `ON DELETE CASCADE` for rule 8).
- Do not change the `company` ORM models — `company.companies.id` remains
  `String(36)` UUID.
