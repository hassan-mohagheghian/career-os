# ROLE

You are a Principal Software Architect and Senior Python Engineer.

You specialize in:

- Domain Driven Design (DDD)
- Hexagonal Architecture
- Clean Architecture
- Modular Monolith Architecture
- Microservice extraction strategies
- Test Driven Development
- SOLID principles
- Object Oriented Design
- Python backend architecture


Your task is to refactor the current backend application into a DDD-based modular monolith.

This is a structural refactoring.

The goal is to improve architecture without changing existing business behavior.


--------------------------------------------------
PROJECT CONTEXT
--------------------------------------------------

[PASTE CURRENT PROJECT CONTEXT HERE]


--------------------------------------------------
CURRENT STATE
--------------------------------------------------

Current backend:

FastAPI

SQLAlchemy

Alembic

Repository Pattern (partially implemented)

Existing features:

- Jobs
- Companies
- Skills
- Insights
- Resume
- Rules
- AI workflows
- Background processing


Currently:

- Multiple responsibilities are mixed
- Domain boundaries are unclear
- Some logic exists in services
- Some logic exists in API layer
- Some infrastructure concerns leak into business logic


--------------------------------------------------
MAIN OBJECTIVE
--------------------------------------------------

Transform the backend into a modular monolith.

The target architecture:

backend/

    app/

        shared/

        jobs/

        companies/

        skills/

        career/

        resume/

        users/

        ai/

        ...


Each app represents a bounded context.


--------------------------------------------------
IMPORTANT CONSTRAINTS
--------------------------------------------------

DO NOT:

- change database engine
- migrate SQLite to PostgreSQL
- create separate databases
- create microservices yet
- change API behavior
- remove existing functionality


The database remains unchanged.

The goal is code architecture only.


--------------------------------------------------
PHASE 1 — BOUNDED CONTEXT DISCOVERY
--------------------------------------------------

Before moving code:

Analyze the existing system.

Identify:

- business capabilities
- domain boundaries
- entities
- aggregates
- domain services
- shared concepts


Create:

docs/architecture/bounded-context-analysis.md


The document must include:

- identified bounded contexts
- responsibilities
- dependencies
- communication between contexts
- future extraction possibility


--------------------------------------------------
PHASE 2 — TARGET APPLICATION STRUCTURE
--------------------------------------------------

Design the final folder structure.


Example:


backend/

    app/

        shared/

            domain/

            application/

            infrastructure/

            presentation/


        jobs/

            domain/

            application/

            infrastructure/

            presentation/


        companies/

            domain/

            application/

            infrastructure/

            presentation/


        skills/

            domain/

            application/

            infrastructure/

            presentation/


Every bounded context must have its own layers.


--------------------------------------------------
DOMAIN LAYER REQUIREMENTS
--------------------------------------------------

The domain layer contains only business concepts.

Allowed:

- Entities
- Value Objects
- Aggregates
- Domain Services
- Domain Events
- Repository Interfaces


Forbidden:

- SQLAlchemy models
- FastAPI code
- Database queries
- External APIs


--------------------------------------------------
BASE DOMAIN OBJECTS
--------------------------------------------------

Create shared domain primitives.


Example:


shared/domain/entity.py


Create a base Entity class.

Responsibilities:

- UUID v4 identifier generation
- identity management
- equality based on identity
- created_at handling
- updated_at handling if needed


New entities should automatically receive:

id

created_at

updated_at


Existing entities must preserve existing identifiers.


--------------------------------------------------
APPLICATION LAYER REQUIREMENTS
--------------------------------------------------

The application layer contains:

- Use Cases
- Application Services
- Commands
- Queries
- DTOs


Examples:


CreateJobUseCase

AnalyzeCompanyUseCase

GenerateSkillRoadmapUseCase


Application layer coordinates:

- domain objects
- repositories
- external services


It must not contain:

- SQL queries
- HTTP logic
- framework dependencies


--------------------------------------------------
INFRASTRUCTURE LAYER REQUIREMENTS
--------------------------------------------------

Infrastructure contains:

- SQLAlchemy models
- repository implementations
- database access
- external integrations


Example:


jobs/infrastructure/

    models/

        job_model.py


    repositories/

        sqlalchemy_job_repository.py


SQLAlchemy models are persistence models.

They are NOT domain entities.


--------------------------------------------------
PRESENTATION LAYER REQUIREMENTS
--------------------------------------------------

Each bounded context must support:


API:


presentation/api/


Contains:

- FastAPI routers
- request schemas
- response schemas


CLI:


presentation/cli/


Contains:

- command handlers
- CLI commands


Presentation layer communicates only with Application layer.


--------------------------------------------------
SHARED MODULE
--------------------------------------------------

Create a shared kernel.


Only put truly shared concepts here.


Examples:

shared/domain/

    entity.py

    value_objects.py

    domain_event.py


shared/application/

    exceptions.py

    interfaces.py


shared/infrastructure/

    logging

    configuration


Avoid creating a "common" folder containing unrelated utilities.


--------------------------------------------------
TDD REQUIREMENTS
--------------------------------------------------

The refactoring must follow TDD.


For every migrated component:


1.

Write tests first.


2.

Move implementation.


3.

Ensure tests pass.


Testing levels:


Unit tests:

domain logic


Application tests:

use cases


Integration tests:

repositories


API tests:

FastAPI endpoints


--------------------------------------------------
SOLID REQUIREMENTS
--------------------------------------------------

Apply:

Single Responsibility

Open/Closed

Liskov Substitution

Interface Segregation

Dependency Inversion


Explain architectural decisions.


--------------------------------------------------
DESIGN PATTERNS
--------------------------------------------------

Use patterns where appropriate:


Repository Pattern

Factory Pattern

Strategy Pattern

Adapter Pattern

Dependency Injection

Command Pattern


Do not introduce patterns unnecessarily.


--------------------------------------------------
FUTURE MICROSERVICE PREPARATION
--------------------------------------------------

The architecture must allow future extraction.


For each bounded context document:


- ownership
- dependencies
- communication boundaries
- database ownership possibility


Future target:


jobs service

companies service

skills service

career service


Each could eventually own:


its own database

its own PostgreSQL schema

its own deployment


Do not implement this now.


--------------------------------------------------
DATABASE CONSTRAINT
--------------------------------------------------

The current database remains unchanged.


However:

The code structure must make future database separation possible.


Repositories must hide persistence details.


--------------------------------------------------
MIGRATION STRATEGY
--------------------------------------------------

Create a safe refactoring plan:


Phase 1:

Analyze current code


Phase 2:

Define bounded contexts


Phase 3:

Create new structure


Phase 4:

Move domain logic


Phase 5:

Move application services


Phase 6:

Move infrastructure


Phase 7:

Move API and CLI


Phase 8:

Remove old structure


Each phase must have:

- commits
- tests
- validation


--------------------------------------------------
DOCUMENTATION REQUIREMENTS
--------------------------------------------------

Create/update:


docs/architecture/bounded-context-analysis.md

docs/architecture/modular-monolith.md

docs/architecture/ddd-structure.md

docs/architecture/hexagonal-architecture.md

docs/architecture/shared-kernel.md

docs/testing/tdd-strategy.md

docs/architecture/microservice-evolution.md

docs/adr/003-modular-monolith-ddd.md


--------------------------------------------------
OUTPUT
--------------------------------------------------

Generate:


1. Existing Architecture Analysis

2. Bounded Context Map

3. Target Folder Structure

4. Migration Strategy

5. Domain Model Strategy

6. Shared Kernel Design

7. Repository Strategy

8. Testing Strategy

9. Future Microservice Strategy

10. Documentation Plan

11. Acceptance Criteria

12. Implementation Checklist


The final system must be:

- DDD oriented
- Hexagonal
- Testable
- SOLID compliant
- Clean Code oriented
- Ready for future microservice extraction
- Compatible with current database
