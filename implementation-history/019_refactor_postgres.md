# ROLE

You are a Principal Database Architect and Senior Backend Engineer.

You specialize in PostgreSQL architecture, database migrations, SQLAlchemy Core, Alembic, and designing scalable data platforms for AI-native applications.

Your task is to migrate the existing application database from SQLite to PostgreSQL.

This is a production migration.

The goal is not only to move data, but to establish a long-term database foundation.


--------------------------------------------------
PROJECT CONTEXT
--------------------------------------------------

[PASTE PROJECT CONTEXT HERE]


--------------------------------------------------
CURRENT DATABASE
--------------------------------------------------

Current:

SQLite

Raw SQL access

Custom migration system

Existing tables:

- jobs
- companies
- company_intelligence
- skills
- skill_roadmaps
- pending_jobs
- pending_companies
- pending_generations


--------------------------------------------------
TARGET DATABASE
--------------------------------------------------

Move to:

PostgreSQL

Running through Docker

Use:

- PostgreSQL latest stable version
- persistent volumes
- environment-based configuration
- health checks
- development and production compatibility


--------------------------------------------------
DATABASE PRINCIPLES
--------------------------------------------------

The new database architecture must support:

- DDD
- Repository Pattern
- SQLAlchemy Core
- Alembic migrations
- UUID identifiers
- AI workflows
- Knowledge Graph future requirements
- Vector search future requirements


--------------------------------------------------
DO NOT
--------------------------------------------------

Do not:

- introduce ORM models
- use SQLAlchemy ORM
- redesign all business entities
- create Graph Database
- remove existing data
- break existing features


--------------------------------------------------
DOCKER REQUIREMENTS
--------------------------------------------------

Design Docker setup.

Create:

docker-compose.yml

Requirements:

PostgreSQL service

Persistent volume

Environment variables

Health checks

Network configuration

Development configuration

Production considerations


Include:

DATABASE_URL

POSTGRES_USER

POSTGRES_PASSWORD

POSTGRES_DB


--------------------------------------------------
SCHEMA MIGRATION
--------------------------------------------------

Analyze existing SQLite schema.

Design PostgreSQL equivalent.

Consider:

- UUID primary keys
- timestamps
- indexes
- constraints
- foreign keys
- unique constraints
- JSONB usage where appropriate


--------------------------------------------------
IDENTIFIER STRATEGY
--------------------------------------------------

Migrate identifiers from integer IDs if needed.

Evaluate UUID usage.

Explain:

- benefits
- migration approach
- compatibility impact


--------------------------------------------------
ALEMBIC DESIGN
--------------------------------------------------

Design Alembic migration system.

Include:

alembic/

versions/

env.py

configuration strategy


Explain:

migration workflow

upgrade

downgrade

rollback

production deployment


--------------------------------------------------
SQLALCHEMY CORE
--------------------------------------------------

Design database access layer using SQLAlchemy Core.

Create:

database connection layer

engine management

session strategy

transaction handling

repository pattern compatibility


--------------------------------------------------
REPOSITORY LAYER
--------------------------------------------------

Design repository abstraction.

Example:

JobRepository

CompanyRepository

SkillRepository


The domain layer must not directly access SQL.


--------------------------------------------------
DATA MIGRATION
--------------------------------------------------

Create a migration strategy from SQLite data to PostgreSQL.

Include:

export strategy

transformation steps

validation

data consistency checks

rollback plan


--------------------------------------------------
FUTURE GRAPH COMPATIBILITY
--------------------------------------------------

Prepare the database for future Knowledge Graph Engine.

Consider future tables:

concept_nodes

concept_edges

concept_aliases

graph_versions

user_progress

learning_paths


Do not implement them now.

Only ensure PostgreSQL architecture can support them.


--------------------------------------------------
SEARCH AND AI PREPARATION
--------------------------------------------------

Prepare for future:

PostgreSQL Full Text Search

pgvector

JSONB metadata

analytics queries


--------------------------------------------------
DOCUMENTATION REQUIREMENTS
--------------------------------------------------

Create or update:


docs/database/postgresql-architecture.md

Include:

- PostgreSQL design
- extensions
- conventions


docs/database/schema-design.md

Include:

- tables
- relationships
- indexes


docs/database/alembic-guide.md

Include:

- migration workflow


docs/migrations/sqlite-to-postgresql.md

Include:

- migration phases
- risks
- rollback


docs/architecture/repository-pattern.md

Include:

- repository boundaries


docs/docker/database-setup.md

Include:

- docker configuration
- local development


docs/adr/002-postgresql-selection.md

Include:

- decision
- alternatives
- reasons


--------------------------------------------------
OUTPUT
--------------------------------------------------

Generate a complete engineering proposal containing:

1. PostgreSQL Architecture

2. Docker Architecture

3. Database Configuration

4. Schema Migration Plan

5. UUID Strategy

6. Alembic Strategy

7. SQLAlchemy Core Strategy

8. Repository Design

9. Data Migration Plan

10. Rollback Strategy

11. Testing Strategy

12. Documentation Updates

13. Acceptance Criteria

14. Implementation Checklist


The result must be production-ready and compatible with future Knowledge Graph and AI systems.
