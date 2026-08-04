# Sprint 19 — Migrate to PostgreSQL with Schema-per-Bounded-Context and Independent Alembic Versioning

## ROLE

You are a Principal Software Architect, PostgreSQL Expert, SQLAlchemy Expert, Alembic Expert, DDD Expert, and Database Architect.

Your task is to redesign the project's persistence architecture.

The project currently uses SQLAlchemy with a separated database layer.

The goal is to migrate the entire system from SQLite to PostgreSQL while redesigning the database layout according to Domain-Driven Design principles.

This migration should prepare the project for future Microservice extraction.

Business behavior must remain unchanged.

--------------------------------------------------
OBJECTIVES
--------------------------------------------------

Migrate the project completely from SQLite to PostgreSQL.

Instead of placing every table into the default schema, each Bounded Context must own its own PostgreSQL schema.

Each Bounded Context should also own its own Alembic migration history.

The architecture should be ready for future Microservice extraction without requiring database restructuring.

--------------------------------------------------
TARGET DATABASE ARCHITECTURE
--------------------------------------------------

Use a single PostgreSQL database.

Inside that database create one schema per Bounded Context.

Example:

job

company

sdk

shared

background

auth

notifications

...

Every SQLAlchemy model must explicitly belong to its corresponding schema.

Never place domain tables inside the default public schema unless absolutely necessary.

--------------------------------------------------
SCHEMA OWNERSHIP

Each Bounded Context owns:

• Tables

• Indexes

• Constraints

• Views

• Functions (if any)

• Triggers (if any)

• Migration history

No Bounded Context should modify another Context's schema.

--------------------------------------------------
SQLALCHEMY

Review every SQLAlchemy model.

Assign the correct schema.

Examples:

__table_args__ = {
    "schema": "job"
}

Move every model into the correct ownership boundary.

Review:

Foreign Keys

Relationships

Indexes

Unique Constraints

Composite Keys

Naming conventions

Everything should remain consistent.

--------------------------------------------------
ALEMBIC

Redesign Alembic.

Each Bounded Context should maintain its own migration history.

Do NOT use a single global alembic_version table.

Instead create one version table per Bounded Context.

Example:

job.alembic_version

company.alembic_version

sdk.alembic_version

background.alembic_version

...

Each Context should be able to evolve independently.

--------------------------------------------------
VERSION LOCATIONS

Separate migration directories.

Example:

database/

    migrations/

        job/

        company/

        sdk/

        background/

        shared/

Configure Alembic to support multiple version locations.

Each migration belongs only to its owning Context.

--------------------------------------------------
MIGRATION RULES

A migration may only modify objects inside its own schema.

Cross-schema modifications are not allowed unless explicitly required and documented.

Avoid coupling between migration histories.

--------------------------------------------------
DATABASE INFRASTRUCTURE

Review the existing database infrastructure.

Update:

Engine configuration

Session management

Metadata

Naming conventions

Migration configuration

Schema creation

Startup initialization

Everything should support schema-aware execution.

--------------------------------------------------
TESTING

All tests must execute against PostgreSQL.

Do NOT use SQLite for testing.

Tests should validate the exact production behavior.

Update:

Unit Tests

Integration Tests

Repository Tests

Migration Tests

Schema Tests

Relationship Tests

--------------------------------------------------
DOCKER

Update Docker Compose.

Provision PostgreSQL.

Automatically initialize:

Schemas

Extensions

Migration execution

Test databases

Development databases

Everything should start with one command.

--------------------------------------------------
CI/CD

Update GitHub Actions.

Run PostgreSQL as a service container.

Execute:

Alembic migrations

Schema creation

Full test suite

Migration validation

No SQLite should remain inside CI.

--------------------------------------------------
BACKGROUND SERVICE

Review the Background application.

Ensure it correctly uses:

Shared SQLAlchemy infrastructure

Shared Engine

Shared Session Factory

The Background service should continue accessing business entities through the shared persistence layer.

Its own execution tables should remain inside the background schema.

--------------------------------------------------
PERFORMANCE

Review indexes.

Review query plans.

Review foreign keys.

Review transactions.

Optimize PostgreSQL-specific features where appropriate.

Examples:

UUID

JSONB

GIN indexes

Partial indexes

CHECK constraints

Generated columns

Use PostgreSQL capabilities whenever beneficial.

--------------------------------------------------
DOCUMENTATION

Update documentation.

Create:

docs/database-architecture.md

docs/postgresql.md

docs/schema-per-bounded-context.md

docs/alembic.md

docs/migrations.md

docs/database-development.md

docs/adr/019-postgresql-migration.md

Document:

Schema ownership

Migration ownership

Naming conventions

Alembic workflow

Developer workflow

Future Microservice migration strategy

--------------------------------------------------
CLEANUP

Remove:

SQLite support

SQLite configuration

SQLite tests

Legacy migration logic

Legacy Alembic configuration

Unused SQLAlchemy compatibility code

--------------------------------------------------
FUTURE-PROOFING

The database architecture must allow a Bounded Context to be extracted into its own Microservice in the future with minimal effort.

A future migration should require moving only:

The schema

Its migration history

Its application service

without redesigning the database.

--------------------------------------------------
ACCEPTANCE CRITERIA

✔ SQLite has been completely removed.

✔ PostgreSQL is the only supported database.

✔ Every Bounded Context owns its own PostgreSQL schema.

✔ Every Bounded Context owns its own Alembic migration history.

✔ Each schema contains its own alembic_version table.

✔ Migration directories are separated per Context.

✔ SQLAlchemy models are schema-aware.

✔ All tests execute on PostgreSQL.

✔ Docker and GitHub Actions support the new architecture.

✔ Documentation is updated.

✔ The architecture is ready for future Microservice extraction.
