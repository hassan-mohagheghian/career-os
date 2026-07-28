# Sprint 06 — Eliminate All Raw SQL and Fully Adopt SQLAlchemy ORM

## ROLE

You are a Principal Python Engineer, SQLAlchemy Expert, Database Architect, and DDD Software Architect.

Your task is to completely eliminate every piece of raw SQL from the project and migrate the entire persistence layer to SQLAlchemy ORM.

This is a full persistence-layer refactor.

No business behavior should change.

--------------------------------------------------
PROJECT CONTEXT
--------------------------------------------------

[PASTE CURRENT PROJECT CONTEXT HERE]

--------------------------------------------------
CURRENT STATE
--------------------------------------------------

The project has already been migrated to:

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic

Database models already exist.

Alembic migrations are working.

However, many parts of the project still execute raw SQL.

Examples include:

SELECT

INSERT

UPDATE

DELETE

JOIN

GROUP BY

ORDER BY

COUNT

EXISTS

ALTER

TEXT SQL

Session.execute(text(...))

Connection.execute(...)

Cursor.execute(...)

Manual SQL string concatenation

Everything must be analyzed.

--------------------------------------------------
OBJECTIVE
--------------------------------------------------

Completely remove every raw SQL statement from the codebase.

The project should use SQLAlchemy ORM exclusively.

Whenever possible use:

Session

select()

update()

delete()

insert()

relationship()

joinedload()

selectinload()

contains_eager()

subqueryload()

exists()

func.*

scalar_subquery()

hybrid properties (when appropriate)

mapped relationships

Only if SQLAlchemy genuinely cannot express a query efficiently may SQLAlchemy's own textual SQL APIs be used—and such cases must be documented and justified. Direct DB driver SQL and handwritten SQL strings should be eliminated.

--------------------------------------------------
ANALYSIS PHASE
--------------------------------------------------

Before changing code:

Scan the entire repository.

Find every occurrence of:

execute(

text(

SELECT

INSERT

UPDATE

DELETE

CREATE

ALTER

DROP

cursor

fetchone

fetchall

fetchmany

connection.execute

raw SQL strings

sqlite-specific syntax

Everything.

Generate a complete inventory.

--------------------------------------------------
REFACTOR STRATEGY
--------------------------------------------------

Refactor incrementally.

Each repository should be migrated separately.

Suggested order:

Shared

↓

Jobs

↓

Companies

↓

Skills

↓

Career

↓

Resume

↓

AI

↓

Remaining contexts

Do not refactor everything at once.

--------------------------------------------------
REPOSITORY LAYER
--------------------------------------------------

Repositories should become true ORM repositories.

Example:

Instead of:

SELECT ...

Use:

select(Job)

Instead of:

UPDATE jobs ...

Use:

update(Job)

Instead of:

DELETE ...

Use:

delete(Job)

Instead of manual joins:

Use relationships.

--------------------------------------------------
MODEL RELATIONSHIPS
--------------------------------------------------

Review every SQLAlchemy model.

If relationships are missing:

Add them.

Use:

relationship()

back_populates

ForeignKey

Proper loading strategies

Avoid unnecessary manual joins.

--------------------------------------------------
QUERY MODERNIZATION
--------------------------------------------------

Replace raw SQL with ORM expressions.

Examples:

COUNT

EXISTS

Pagination

Sorting

Filtering

Aggregations

Window functions (if needed)

Everything should use SQLAlchemy's expression language.

--------------------------------------------------
SESSION MANAGEMENT
--------------------------------------------------

Review session lifecycle.

Use proper:

Session

Transaction boundaries

Commit

Rollback

Context managers

Avoid manual connection handling.

--------------------------------------------------
PERFORMANCE
--------------------------------------------------

Avoid introducing N+1 queries.

Use:

joinedload()

selectinload()

contains_eager()

when appropriate.

Review every repository for efficiency.

--------------------------------------------------
SQL DIALECT
--------------------------------------------------

Remove every SQLite-specific implementation.

Ensure full PostgreSQL compatibility.

The ORM should remain database-agnostic whenever practical.

--------------------------------------------------
TESTING
--------------------------------------------------

Existing behavior must remain identical.

Add or update tests for:

Repositories

CRUD operations

Filtering

Pagination

Sorting

Transactions

Relationship loading

Error handling

--------------------------------------------------
VALIDATION
--------------------------------------------------

After refactoring:

Search the repository again.

There should be:

NO

SELECT ...

INSERT ...

UPDATE ...

DELETE ...

raw SQL strings

cursor.execute()

connection.execute()

manual SQL generation

except for explicitly documented ORM text fallbacks.

--------------------------------------------------
CODE QUALITY
--------------------------------------------------

Follow:

DDD

SOLID

Repository Pattern

Clean Code

Hexagonal Architecture

Type safety

Python best practices

Repositories must expose domain-friendly APIs.

Business logic must never build SQL.

--------------------------------------------------
DOCUMENTATION
--------------------------------------------------

Create or update:

docs/database/sqlalchemy-orm.md

docs/database/repository-pattern.md

docs/database/query-guidelines.md

docs/architecture/persistence-layer.md

docs/adr/007-full-sqlalchemy-orm.md

Document:

Repository conventions

Query guidelines

Relationship guidelines

Session lifecycle

Performance recommendations

When raw SQL is acceptable (if ever)

--------------------------------------------------
OUTPUT
--------------------------------------------------

Produce:

1. Raw SQL Inventory

2. Migration Strategy

3. Repository Refactor Plan

4. ORM Improvements

5. Relationship Improvements

6. Session Management Improvements

7. Performance Improvements

8. Testing Plan

9. Documentation Plan

10. Final Validation Report

--------------------------------------------------
ACCEPTANCE CRITERIA
--------------------------------------------------

✔ Every repository uses SQLAlchemy ORM.

✔ No handwritten SQL remains in business code.

✔ Relationships replace manual joins whenever possible.

✔ Sessions are properly managed.

✔ Repository interfaces remain stable.

✔ Existing functionality is preserved.

✔ Tests pass.

✔ The project no longer depends on raw SQL for normal CRUD and query operations.
