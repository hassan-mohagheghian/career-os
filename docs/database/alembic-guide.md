# Alembic Migration Guide

## Overview

Alembic manages database schema migrations. It replaces the custom `migrations.py` approach with versioned, reversible migration scripts.

## Setup

- **Config**: `alembic.ini`
- **Migrations**: `alembic/versions/`
- **Environment**: `alembic/env.py`

## Common Commands

### Check current migration state
```bash
alembic current
```

### View migration history
```bash
alembic history
```

### Generate a new migration
```bash
alembic revision --autogenerate -m "description of changes"
```

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

1. **Modify ORM models** in `infrastructure/database/models/`
2. **Generate migration**: `alembic revision --autogenerate -m "description"`
3. **Review** the generated file in `alembic/versions/`
4. **Test** the migration: `alembic upgrade head && alembic downgrade -1`
5. **Commit** the migration file

## Review Process

Always review auto-generated migrations before committing:

- Check for unintended column type changes
- Verify index creation/deletion
- Ensure data migrations are handled separately
- Test both upgrade and downgrade paths

## How Models Connect to Alembic

Alembic's `env.py` imports the `Base` object and all models via `infrastructure.database.models`. The `target_metadata = Base.metadata` line tells Alembic to inspect all registered tables for autogeneration.

## Data Migrations

For data transformations (backfills, renames, etc.), use Alembic's `op.execute()` with raw SQL or Python code in the `upgrade()` function:

```python
def upgrade():
    op.add_column('table', sa.Column('new_col', sa.Text()))
    op.execute("UPDATE table SET new_col = old_col")
```

## Troubleshooting

### "Table already exists" error
The database already has the table. Use `alembic stamp head` to mark it as current.

### Migration doesn't detect changes
Ensure all models are imported in `infrastructure/database/models/__init__.py`.

### SQLite-specific issues
- Use `render_as_batch=True` in `env.py` for ALTER TABLE operations
- SQLite doesn't support DROP COLUMN (use batch mode or recreate table)
