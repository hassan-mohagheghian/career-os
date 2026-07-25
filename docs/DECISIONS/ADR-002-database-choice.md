# ADR-002: Database Choice (SQLite, No ORM)

## Context

Need persistent storage for jobs, companies, skills, resumes, and intelligence data. Single-user application.

## Decision

SQLite with raw SQL queries, no ORM.

## Alternatives

- **SQLAlchemy ORM**: Rejected — adds abstraction layer, harder to debug queries, slower for simple CRUD
- **PostgreSQL**: Rejected — requires server setup, overkill for single-user
- **MongoDB**: Rejected — relational data fits SQL better, no schema flexibility needed

## Consequences

**Positive:**
- Zero configuration — database file just exists
- Full control over queries and schema
- Easy to inspect with `sqlite3` CLI
- WAL mode for concurrent reads during writes
- Inline migrations (no Alembic complexity)

**Negative:**
- Manual query writing (more verbose)
- No type safety at query level
- Manual connection management (always close after use)
