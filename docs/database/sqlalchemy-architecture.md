# SQLAlchemy Architecture

## Overview

The persistence layer uses SQLAlchemy 2.x with the declarative base pattern. All database access goes through repository implementations that use SQLAlchemy sessions, hiding the underlying database details from the domain and application layers.

## Key Components

### Engine & Session

- **Engine**: `infrastructure/database/sqlalchemy_config.py` — creates the SQLAlchemy engine with SQLite-specific PRAGMAs (WAL, busy_timeout, foreign_keys)
- **SessionLocal**: Session factory bound to the engine, creates request-scoped sessions
- **get_session()**: FastAPI dependency that yields a session with auto-commit/rollback

### Declarative Base

```python
# infrastructure/database/sqlalchemy_config.py
class Base(DeclarativeBase):
    pass
```

All ORM models inherit from this base. The metadata is used by Alembic for autogeneration.

### ORM Models

Located in `infrastructure/database/models/`:

| File | Tables |
|------|--------|
| `job_model.py` | `jobs` |
| `skill_model.py` | `skills`, `skill_aliases`, `skill_relationships` |
| `company_model.py` | `companies`, `company_intelligence`, `company_links` |
| `pending_model.py` | `pending_jobs`, `pending_companies`, `pending_generations` |
| `misc_models.py` | `summaries`, `resumes`, `skill_roadmaps`, `skill_roadmap_progress`, `skill_roadmap_jobs`, `rules`, `cities` |

### Domain-to-Database Mapping

Located in `infrastructure/database/mappers.py`:

- `*_model_to_dict()` — converts ORM model to domain dictionary
- `dict_to_*_model()` — converts domain dictionary to ORM model

Mapping happens in the infrastructure layer, keeping the domain layer clean.

### Repository Pattern

- **Domain interfaces**: `domain/repositories/` (ABCs)
- **SQLAlchemy implementations**: `infrastructure/database/sa_*_repository.py`

Repositories accept a `Session` in their constructor and use it for all database operations.

## Session Lifecycle

```
Request arrives
  → get_session() yields a new Session
    → Route handler uses repository (which uses the session)
      → Session commits on success, rolls back on error
        → Session closes in finally block
```

## Testing

Tests use in-memory SQLite databases:

```python
@pytest.fixture
def sa_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

## Future PostgreSQL Migration

When migrating to PostgreSQL:

1. Change `sqlalchemy.url` in `alembic.ini`
2. Update `connect_args` in `sqlalchemy_config.py` (remove SQLite-specific settings)
3. Regenerate Alembic migration with `--sql` mode to compare
4. All repository code remains unchanged (SQLAlchemy abstracts the dialect)
