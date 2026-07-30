# SQLAlchemy Architecture

## Overview

The persistence layer uses SQLAlchemy 2.x with the declarative base pattern. All database access goes through repository implementations that use SQLAlchemy sessions, hiding the underlying database details from the domain and application layers.

The database uses a **schema-per-bounded-context** architecture, isolating each domain's tables in its own PostgreSQL schema. This enables independent versioning via Alembic and clean separation of concerns, while allowing cross-schema foreign key relationships where needed.

## Key Components

### Engine & Session

- **Engine**: `shared/infrastructure/database/sqlalchemy_config.py` — auto-detects SQLite vs PostgreSQL from the `DATABASE_URL` environment variable
  - **SQLite**: Applies WAL mode, busy_timeout, foreign_keys PRAGMAs. Uses `schema_translate_map` to strip schema qualifiers (PostgreSQL-only concept)
  - **PostgreSQL**: Uses psycopg as the driver, creates schemas via `ensure_schemas()`, no schema translation needed
- **SessionLocal**: Session factory bound to the engine, creates request-scoped sessions
- **get_session()**: FastAPI dependency that yields a session with auto-commit/rollback

### Database URL Configuration

```python
# shared/infrastructure/config/app_config.py
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DB_PATH}"
```

- Local dev: defaults to SQLite (no config needed)
- Production/CI: set `DATABASE_URL=postgresql+psycopg://user:pass@host/dbname`

### Schema Auto-Detection

```python
# shared/infrastructure/database/sqlalchemy_config.py
if url.startswith("postgresql"):
    # PostgreSQL: create schemas, no translation needed
    engine = create_engine(url, pool_size=10, max_overflow=20)
    ensure_schemas(engine)
else:
    # SQLite: strip schema qualifiers via translate map
    engine = create_engine(url, connect_args=connect_args)
    engine = engine.execution_options(schema_translate_map={
        "job": None, "company": None, "skill": None, "shared": None
    })
```

### Declarative Base

```python
# shared/infrastructure/database/sqlalchemy_config.py
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    })
```

All ORM models inherit from this base. The naming convention ensures consistent constraint naming across all schemas.

### Schema-Per-Context

| Schema | Context | Tables |
|--------|---------|--------|
| `job` | Job Processing | `jobs`, `summaries`, `resumes`, `generation_history` |
| `company` | Company Intelligence | `companies`, `company_intelligence`, `company_links` |
| `skill` | Skills Management | `skills`, `skill_aliases`, `skill_relationships`, `skill_roadmaps`, `skill_roadmap_progress`, `skill_roadmap_jobs` |
| `shared` | Shared/Cross-Cutting | `rules`, `cities` |

Models declare their schema via `__table_args__`:

```python
class JobModel(Base):
    __tablename__ = "jobs"
    __table_args__ = {"schema": "job"}
```

Foreign keys use fully-qualified table names:

```python
company_id = Column(UUID, ForeignKey("company.companies.id"), nullable=True)
```

### ORM Models

Located in context-specific model files:

| File | Schema | Tables |
|------|--------|--------|
| `jobs/infrastructure/models/job_model.py` | `job` | `jobs` |
| `skills/infrastructure/models/skill_model.py` | `skill` | `skills`, `skill_aliases`, `skill_relationships` |
| `companies/infrastructure/models/company_model.py` | `company` | `companies`, `company_intelligence`, `company_links` |
| `shared/infrastructure/database/models/misc_models.py` | `job`, `skill`, `shared` | `summaries`, `resumes`, `skill_roadmaps`, `skill_roadmap_progress`, `skill_roadmap_jobs`, `rules`, `cities` |

All models are re-exported from `shared/infrastructure/database/models/__init__.py` for Alembic auto-discovery.

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

Tests use in-memory SQLite databases by default. For PostgreSQL testing, set `DATABASE_URL`:

```python
@pytest.fixture
def sa_session():
    engine = create_engine("sqlite:///:memory:")
    engine = engine.execution_options(schema_translate_map=schema_translate_map())
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

The `schema_translate_map` strips PostgreSQL schema qualifiers when running against SQLite, allowing the same model definitions to work with both databases. CI runs tests with both SQLite (default) and PostgreSQL (via service container + `DATABASE_URL` env).