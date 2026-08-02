# Alembic Migration Guide

## Overview

Alembic manages database schema migrations across four bounded contexts. Each context has its own migration directory and Alembic revision line, allowing independent schema versioning per domain.

## Directory Structure

```
apps/alembic/
├── alembic.ini
├── env.py              # shared environment config
├── job/
│   └── versions/       # job schema migrations
├── company/
│   └── versions/       # company schema migrations
├── skill/
│   └── versions/       # skill schema migrations
└── shared/
    └── versions/       # shared schema migrations
```

## Setup

- **Config**: `apps/alembic/alembic.ini`
- **Environment**: `apps/alembic/env.py`
- **Version locations**: configured per context in `alembic.ini`

```ini
version_locations = %(here)s/job/versions %(here)s/company/versions %(here)s/skill/versions %(here)s/shared/versions
```

## Schema Configuration

Each bounded context owns a PostgreSQL schema:

| Context | Schema | Migration Dir |
|---------|--------|---------------|
| Job | `job` | `apps/alembic/job/` |
| Company | `company` | `apps/alembic/company/` |
| Skill | `skill` | `apps/alembic/skill/` |
| Shared | `shared` | `apps/alembic/shared/` |

The `env.py` imports all models from `shared.infrastructure.database.models` so Alembic can autogenerate migrations for all schemas. `include_schemas=True` ensures schema-aware operations.

## Common Commands

Run all commands from the `apps/alembic/` directory:

### Check current migration state for all contexts

```bash
cd apps/alembic
alembic current
```

### View migration history

```bash
alembic history
```

### Generate a new migration (autogenerate for all schemas)

```bash
alembic revision --autogenerate -m "description of changes"
```

This creates a new migration file in the appropriate version directory based on which tables changed.

### Apply pending migrations

```bash
alembic upgrade head
```

### Rollback one migration

```bash
alembic downgrade -1
```

### Rollback to a specific revision

```bash
alembic downgrade <revision_id>
```

### Stamp a database as up-to-date (without running migrations)

```bash
alembic stamp head
```

## Migration Workflow

1. **Modify ORM models** in the appropriate context model file
2. **Generate migration**: `alembic revision --autogenerate -m "description"`
3. **Review** the generated file in the relevant `versions/` directory
4. **Test** the migration: `alembic upgrade head && alembic downgrade -1`
5. **Commit** the migration file

## Review Process

Always review auto-generated migrations before committing:

- Check for unintended column type changes
- Verify index creation/deletion
- Ensure schema operations are correct (CREATE SCHEMA, SET search_path)
- Test both upgrade and downgrade paths
- Verify cross-schema foreign key references

## How Models Connect to Alembic

Alembic's `env.py` imports the `Base` object and all models via `shared.infrastructure.database.models`. The `target_metadata = Base.metadata` line tells Alembic to inspect all registered tables across all schemas for autogeneration.

## Data Migrations

For data transformations (backfills, renames, etc.), use Alembic's `op.execute()` with raw SQL or Python code in the `upgrade()` function:

```python
def upgrade():
    op.add_column('jobs', sa.Column('new_col', sa.Text()), schema='job')
    op.execute("UPDATE job.jobs SET new_col = old_col")
```

## Running Migrations with Docker Compose

```bash
docker-compose up -d postgres
docker-compose up alembic-migrate
```

The `alembic-migrate` service runs `alembic upgrade head` and exits.

## Troubleshooting

### "Table already exists" error
The database already has the table. Use `alembic stamp head` to mark it as current.

### Migration doesn't detect changes
Ensure all models are imported in `shared/infrastructure/database/models/__init__.py`.

### SQLite-specific issues
- SQLite doesn't support `CREATE SCHEMA` — migrations must be run against PostgreSQL
- Test migrations locally using Docker Compose's postgres service
- For SQLite development, the `schema_translate_map` handles schema qualifiers at runtime

### Cross-schema foreign key confusion
Alembic may reorder migration creation. If a migration references a table from another schema created in a different migration file, ensure the referenced migration runs first by specifying `depends_on` in the revision header.