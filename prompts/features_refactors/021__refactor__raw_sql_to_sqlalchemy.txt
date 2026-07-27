# ROLE

You are a Principal Python Backend Engineer specialized in:

- FastAPI
- SQLAlchemy 2.x
- Alembic
- Database refactoring
- Domain Driven Design
- Hexagonal Architecture
- Legacy code modernization


Your task is to completely refactor the existing backend persistence layer.

The goal is to remove direct raw SQL usage from the application code and migrate database operations to SQLAlchemy-based persistence.


--------------------------------------------------
PROJECT CONTEXT
--------------------------------------------------

[PASTE CURRENT PROJECT CONTEXT HERE]


--------------------------------------------------
CURRENT STATE
--------------------------------------------------

The project already has:

- FastAPI backend
- SQLAlchemy installed
- Alembic configured
- SQLAlchemy database models created
- Existing database migration history

However:

- Some raw SQL queries still exist
- Some database operations bypass SQLAlchemy
- Existing migration files may contain manual SQL operations
- Some repositories/services directly interact with SQL


--------------------------------------------------
MAIN OBJECTIVE
--------------------------------------------------

Refactor the complete backend persistence layer.

After this migration:

The application must use SQLAlchemy as the only database access layer.


Allowed:

- SQLAlchemy ORM
- SQLAlchemy Core expressions
- SQLAlchemy text() only when absolutely required


Not allowed:

- Direct database connections
- Direct cursor usage
- Manual SQL execution from business/application code
- Raw SQL strings scattered throughout the project


--------------------------------------------------
IMPORTANT PRINCIPLE
--------------------------------------------------

Follow this priority:


1.

SQLAlchemy ORM queries


Example:

select()

where()

join()

relationship loading

order_by()

group_by()

update()

delete()



2.

SQLAlchemy Core expressions



3.

Raw SQL through SQLAlchemy execution only when required.



Raw SQL should be considered an exception.

Every raw SQL usage must have documentation explaining why SQLAlchemy cannot handle the case.


--------------------------------------------------
ANALYSIS PHASE
--------------------------------------------------

Before changing code:


Analyze the entire codebase.

Find:

- raw SQL queries
- sqlite specific queries
- direct connections
- cursor usage
- database helpers
- migration scripts
- repository implementations
- service layer database access


Create a report:


docs/database/raw-sql-analysis.md


The report must contain:

- file location
- query purpose
- affected table
- affected domain
- operation type
- migration strategy


Classify each query:


READ:

- fetch one
- fetch many
- search
- filtering
- sorting


WRITE:

- insert
- update
- delete


SCHEMA:

- create table
- alter table
- indexes
- constraints


--------------------------------------------------
QUERY MIGRATION
--------------------------------------------------

Refactor every application query.


Examples:


Before:


SELECT *
FROM jobs
WHERE company_id = ?



After:


select(JobModel)
.where(JobModel.company_id == company_id)



--------------------------------------------------

Before:


UPDATE jobs
SET status = ?
WHERE id = ?



After:


update(JobModel)
.where(JobModel.id == job_id)
.values(status=status)



--------------------------------------------------

Before:


DELETE FROM jobs
WHERE id = ?



After:


delete(JobModel)
.where(JobModel.id == job_id)



--------------------------------------------------
DOMAIN BOUNDARY
--------------------------------------------------

Maintain DDD separation.


Do NOT put SQLAlchemy models inside domain.


Structure:


domain/

    entities/


application/

    use_cases/


infrastructure/

    persistence/

        models/

            JobModel

            CompanyModel

        repositories/

            SQLAlchemyJobRepository


--------------------------------------------------
REPOSITORY REFACTORING
--------------------------------------------------

Every database operation must go through repositories.


Example:


Domain interface:


JobRepository


Infrastructure implementation:


SQLAlchemyJobRepository


Repositories are responsible for:

- queries
- persistence
- transactions
- mapping


--------------------------------------------------
MODEL MAPPING
--------------------------------------------------

Maintain separation:


Domain Entity

<->

SQLAlchemy Persistence Model



Create explicit mapping functions if needed.


Example:


JobEntity

to

JobModel


and:


JobModel

to

JobEntity


--------------------------------------------------
TRANSACTION MANAGEMENT
--------------------------------------------------

Standardize transaction handling.


Define:

- session lifecycle
- commit strategy
- rollback strategy


Avoid:

- random commits
- hidden transactions


--------------------------------------------------
MIGRATION SYSTEM REFACTOR
--------------------------------------------------

Review existing custom migration files.


Move migration responsibility completely to Alembic.


Analyze:

- table creation
- table alteration
- column changes
- indexes
- constraints
- data migrations


Convert old migration logic into proper Alembic migrations.


Requirements:


Every schema change must exist as:

alembic revision


with:


upgrade()


downgrade()



--------------------------------------------------
DATABASE MODEL VALIDATION
--------------------------------------------------

Verify that SQLAlchemy models correctly represent:

- existing database tables
- relationships
- indexes
- constraints


Check:

- table names
- columns
- nullable fields
- defaults
- foreign keys


--------------------------------------------------
TESTING REQUIREMENTS
--------------------------------------------------

Before and after migration:

Run tests for:


CRUD operations:

- create
- read
- update
- delete


Repositories:

- unit tests
- integration tests


Migration:

- upgrade
- downgrade


Data integrity:

- record counts
- relationships


--------------------------------------------------
DOCUMENTATION REQUIREMENTS
--------------------------------------------------

Create/update:


docs/database/raw-sql-analysis.md

Include:

- all discovered SQL usage
- migration status


docs/database/sqlalchemy-query-guide.md

Include:

- query conventions
- allowed patterns


docs/migrations/sqlalchemy-refactor.md

Include:

- migration steps
- completed areas
- remaining work


docs/architecture/persistence-rules.md

Include:

- database access rules
- repository rules
- forbidden patterns


docs/adr/003-sqlalchemy-only-persistence.md

Include:

- decision
- alternatives
- reasoning


--------------------------------------------------
OUTPUT
--------------------------------------------------

Generate:

1. Complete raw SQL inventory

2. Refactoring strategy

3. File-by-file migration plan

4. Repository migration plan

5. SQLAlchemy query replacement examples

6. Migration conversion plan

7. Testing plan

8. Documentation updates

9. Acceptance criteria

10. Implementation checklist


The final system must use SQLAlchemy as the single persistence technology.

Raw SQL is allowed only through SQLAlchemy and only when technically justified.
