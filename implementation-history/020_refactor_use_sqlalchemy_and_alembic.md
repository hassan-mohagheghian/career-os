# ROLE

You are a Principal Software Architect and Senior Python Backend Engineer.

You specialize in:

- FastAPI architectures
- SQLAlchemy 2.x
- Alembic migrations
- Domain Driven Design (DDD)
- Hexagonal Architecture
- Clean Architecture
- Database migrations
- Legacy system modernization


Your task is to analyze the existing FastAPI backend and migrate the current database access and migration approach to a professional SQLAlchemy + Alembic based persistence architecture.

This is NOT a database migration yet.

The database engine remains SQLite for now.

The goal of this phase is to prepare the persistence layer correctly before migrating to PostgreSQL.


--------------------------------------------------
PROJECT CONTEXT
--------------------------------------------------

[PASTE CURRENT PROJECT CONTEXT HERE]


--------------------------------------------------
CURRENT STATE
--------------------------------------------------

Current system:

Backend:
- FastAPI (recently migrated from Flask)

Database:
- SQLite

Current persistence:
- Raw SQL queries
- Custom migration handling
- Direct database access in parts of the codebase


--------------------------------------------------
MAIN OBJECTIVE
--------------------------------------------------

Introduce:

- SQLAlchemy 2.x
- SQLAlchemy ORM models
- Alembic migration management
- Repository-based persistence layer


The final architecture must support:

- DDD
- Hexagonal Architecture
- Future PostgreSQL migration
- Future Knowledge Graph implementation
- AI-driven features


--------------------------------------------------
IMPORTANT REQUIREMENTS
--------------------------------------------------

Before any modification:

1. Create a clean git commit.

The commit should represent the stable FastAPI migration state.

Example:

"chore: migrate backend from Flask to FastAPI"


2. Create a complete SQLite database backup.

The backup must include:

- schema
- data
- indexes
- constraints


The backup must be stored safely.

Document:

- backup location
- restore procedure
- validation steps


--------------------------------------------------
ARCHITECTURAL REQUIREMENTS
--------------------------------------------------

Follow strict separation:

Domain models are NOT SQLAlchemy models.


The architecture should be:


Domain Layer:

Contains:

- Entities
- Value Objects
- Domain Services
- Business Rules


Application Layer:

Contains:

- Use Cases
- Commands
- Queries
- Application Services


Infrastructure Layer:

Contains:

- SQLAlchemy Models
- Database Session
- Repository Implementations
- Persistence Mapping


Example:


domain/

    skill.py
    job.py


application/

    create_skill.py


infrastructure/

    database/

        models/

            skill_model.py

        repositories/

            sqlalchemy_skill_repository.py



--------------------------------------------------
SQLALCHEMY MODEL DESIGN
--------------------------------------------------

Create SQLAlchemy ORM models.

Requirements:

- SQLAlchemy 2.x style
- Declarative models
- Type annotations
- Proper relationships
- Index definitions
- Constraints


The SQLAlchemy models represent:

database tables only.


They are NOT domain entities.


--------------------------------------------------
DOMAIN TO DATABASE MAPPING
--------------------------------------------------

Design mapping strategy between:

Domain Entities

and

SQLAlchemy ORM Models


Example:

Domain:

Skill Entity


maps to:


Infrastructure:

SkillModel


Explain:

- conversion rules
- where mapping happens
- ownership of transformations


--------------------------------------------------
REPOSITORY PATTERN
--------------------------------------------------

Implement repository abstraction.


Domain defines interfaces:


SkillRepository


Infrastructure implements:


SQLAlchemySkillRepository


Repositories must hide:

- SQLAlchemy
- sessions
- queries
- database details


--------------------------------------------------
DATABASE SESSION MANAGEMENT
--------------------------------------------------

Design:

- engine creation
- session lifecycle
- transaction handling
- dependency injection in FastAPI


Support:

- request scoped sessions
- testing sessions


--------------------------------------------------
ALEMBIC SETUP
--------------------------------------------------

Replace custom migration system with Alembic.


Design:

alembic/

    versions/

    env.py


Requirements:

- automatic migration generation
- upgrade
- downgrade
- version tracking


Explain:

- how models are connected to Alembic
- how migrations are reviewed
- how migrations are applied


--------------------------------------------------
MIGRATION STRATEGY
--------------------------------------------------

Create a phased migration plan.


Phase 1:

Install dependencies

Phase 2:

Create SQLAlchemy Base

Phase 3:

Create database models

Phase 4:

Configure Alembic

Phase 5:

Generate initial migration

Phase 6:

Validate against existing SQLite database

Phase 7:

Remove old migration mechanism


For each phase define:

- tasks
- risks
- validation criteria


--------------------------------------------------
QUERY STRATEGY
--------------------------------------------------

Define query approach.

Default:

Use SQLAlchemy ORM queries.


Examples:

- select()
- relationship loading
- filtering
- pagination


For complex cases:

Allow SQLAlchemy Core expressions.

Do NOT directly use database connections.


The application should never manually manage:

- raw connections
- cursors
- transactions


--------------------------------------------------
RAW SQL POLICY
--------------------------------------------------

Raw SQL is allowed only when:

- ORM/query builder cannot efficiently express the query
- performance requires it
- database-specific features are needed


Even then:

Use SQLAlchemy execution mechanisms.

Do NOT bypass SQLAlchemy.


--------------------------------------------------
TESTING
--------------------------------------------------

Create testing strategy for:

- ORM models
- repositories
- migrations
- database transactions


Include:

- SQLite test database strategy
- migration tests
- repository tests


--------------------------------------------------
DOCUMENTATION REQUIREMENTS
--------------------------------------------------

Create or update:


docs/database/sqlalchemy-architecture.md

Include:

- ORM strategy
- model organization
- session handling


docs/database/alembic-guide.md

Include:

- migration workflow
- commands
- review process


docs/architecture/domain-persistence-mapping.md

Include:

- domain model vs persistence model
- mapping strategy


docs/architecture/repository-pattern.md

Include:

- repository interfaces
- implementations


docs/migrations/raw-sql-to-alembic.md

Include:

- migration process
- risks
- rollback strategy


docs/adr/002-sqlalchemy-alembic-selection.md

Include:

- decision
- alternatives
- reasoning


--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

Generate a complete engineering migration proposal.

Include:

1. Current Persistence Analysis

2. Target Persistence Architecture

3. SQLAlchemy Model Strategy

4. Domain Mapping Strategy

5. Repository Architecture

6. Alembic Migration Design

7. Database Session Design

8. Migration Steps

9. Backup Strategy

10. Testing Strategy

11. Documentation Updates

12. Risks

13. Acceptance Criteria

14. Implementation Checklist


The proposal must be production-ready and compatible with future PostgreSQL migration.
