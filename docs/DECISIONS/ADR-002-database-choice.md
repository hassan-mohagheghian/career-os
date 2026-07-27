# ADR-002: Database Choice (SQLite + SQLAlchemy ORM)

## Context

Need persistent storage for jobs, companies, skills, resumes, and intelligence data. Single-user application.

## Decision

SQLite with SQLAlchemy ORM for all database access. Alembic for migrations.

## Alternatives

- **SQLAlchemy ORM**: Rejected — adds abstraction layer, harder to debug queries, slower for simple CRUD
- **PostgreSQL**: Rejected — requires server setup, overkill for single-user
- **MongoDB**: Rejected — relational data fits SQL better, no schema flexibility needed

## Consequences

**Positive:**
- Zero configuration — database file just exists
- SQLAlchemy ORM provides type safety and clean abstractions
- Alembic handles schema migrations cleanly
- Easy to inspect with `sqlite3` CLI
- WAL mode for concurrent reads during writes

**Negative:**
- ORM adds abstraction layer (but provides type safety)
- Alembic adds migration complexity (but ensures clean schema evolution)
