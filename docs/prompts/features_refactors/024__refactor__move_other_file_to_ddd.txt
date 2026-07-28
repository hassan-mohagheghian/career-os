# ROLE

You are a Principal Software Architect specialized in:

- Domain Driven Design
- Hexagonal Architecture
- Modular Monoliths
- FastAPI architecture
- Large-scale Python refactoring
- Clean Architecture


Your task is to refactor the existing backend structure after the initial bounded context extraction.

The project already contains bounded contexts such as:

- jobs
- companies
- skills
- career
- resume
- rules

However, many existing folders still contain mixed responsibilities.

Your responsibility is to analyze every remaining module and move it into the correct bounded context or shared kernel.


--------------------------------------------------
PROJECT CONTEXT
--------------------------------------------------

[PASTE CURRENT PROJECT CONTEXT HERE]


--------------------------------------------------
CURRENT PROBLEM
--------------------------------------------------

The project currently has mixed folders such as:


api/

core/

schemas/

services/

scripts/

prompts/

workers/

processes/


These folders contain code belonging to different domains.


The goal is:

Move ownership from technical folders to business boundaries.


--------------------------------------------------
MAIN PRINCIPLE
--------------------------------------------------

The new structure must follow:


Business Capability > Technical Layer


Wrong:


api/jobs.py

services/jobs.py

schemas/jobs.py


Correct:


jobs/

    presentation/

        api/

        cli/


    application/

        services/

        use_cases/


    domain/

        entities/

        value_objects/

        repositories/


    infrastructure/

        database/

        workers/

        external/


--------------------------------------------------
PHASE 1 — COMPLETE CODE INVENTORY
--------------------------------------------------

Before moving anything:


Analyze every file in:


api/

core/

schemas/

services/

scripts/

prompts/

workers/

processes/


Create:


docs/architecture/code-ownership-map.md


For every file document:


- current location
- responsibility
- business domain
- target bounded context
- target layer


Example:


api/v1/company.py


Current:

global API


Target:


companies/presentation/api/company.py



--------------------------------------------------
PHASE 2 — API ROUTER MIGRATION
--------------------------------------------------

Analyze:


api/v1/


Move every router into its owning context.


Examples:


Company API:


companies/

    presentation/

        api/

            company_router.py



Job API:


jobs/

    presentation/

        api/

            job_router.py



Skill API:


skills/

    presentation/

        api/

            skill_router.py



Shared APIs:


Only truly cross-domain APIs may go into:


shared/presentation/api/


Examples:

- health check
- system status
- authentication middleware


Do not create a dumping ground.


--------------------------------------------------
PHASE 3 — CORE FOLDER REFACTOR
--------------------------------------------------

Analyze:


core/


Separate responsibilities.


Examples:


Database:


Move to:


shared/infrastructure/database/


Queue:


If domain-specific:


move to owning context.


If global:


shared/infrastructure/queue/


Configuration:


shared/infrastructure/config/


Logging:


shared/infrastructure/logging/


Do not keep a generic core folder.


--------------------------------------------------
PHASE 4 — SCHEMA MIGRATION
--------------------------------------------------

Analyze all schemas:


schemas/


Move schemas according to ownership.


Example:


CompanyCreate

CompanyResponse


Move to:


companies/presentation/api/schemas/


JobPendingSchema


Move to:


jobs/presentation/api/schemas/


Shared DTOs:


shared/application/dto/


Important:


Pydantic API schemas are NOT domain entities.


Keep separation:


API Schema

↓

Application DTO

↓

Domain Entity



--------------------------------------------------
PHASE 5 — SERVICES MIGRATION
--------------------------------------------------

Analyze:


services/


Move each service based on responsibility.


Examples:


job_worker.py


Target:


jobs/infrastructure/workers/


generation_service.py


Target:


resume/application/services/


company_analyzer.py


Target:


companies/application/services/


Repository implementations:


Move to:


<context>/infrastructure/repositories/


--------------------------------------------------
PHASE 6 — PROMPT AND AI RESOURCE MIGRATION
--------------------------------------------------

Analyze:


prompts/


Classify:


Job processing prompts


Move:


jobs/infrastructure/ai/prompts/


Company prompts:


companies/infrastructure/ai/prompts/


Skill prompts:


skills/infrastructure/ai/prompts/


Shared AI infrastructure:


shared/infrastructure/ai/


Do not mix business prompts.


--------------------------------------------------
PHASE 7 — SCRIPT AND PROCESS MIGRATION
--------------------------------------------------

Analyze:


scripts/


processes/


Every script must have ownership.


Examples:


analyze_job.py


Move to:


jobs/application/use_cases/


backfill_jobs.py


Move to:


jobs/application/commands/


roadmap_generation.py


Move to:


skills/application/use_cases/


Scripts should become:

- application commands
- CLI commands
- scheduled jobs


Avoid standalone scripts containing business logic.


--------------------------------------------------
PHASE 8 — PRESENTATION LAYER
--------------------------------------------------

Every bounded context must have:


presentation/


    api/


        routers/

        schemas/


    cli/


        commands/


The presentation layer can depend on:


application layer


It must not directly access:


database

repositories

external APIs


--------------------------------------------------
PHASE 9 — INFRASTRUCTURE LAYER
--------------------------------------------------

Each context should have:


infrastructure/


    database/


    repositories/


    workers/


    external/


    ai/


Infrastructure contains:

- FastAPI integrations if framework-specific
- SQLAlchemy models
- repository implementations
- external clients


--------------------------------------------------
PHASE 10 — SHARED KERNEL REVIEW
--------------------------------------------------

Create or update:


shared/


Only move truly shared concepts.


Allowed examples:


shared/domain/

    entity.py

    value_objects.py

    events.py


shared/application/

    exceptions.py

    interfaces.py


shared/infrastructure/

    logging/

    configuration/


Do not move domain-specific logic here.


--------------------------------------------------
ARCHITECTURE RULES
--------------------------------------------------

Dependency direction:


presentation

↓

application

↓

domain


Infrastructure implements interfaces defined by domain/application.


Domain must never depend on:

FastAPI

SQLAlchemy

Pydantic

CLI


--------------------------------------------------
TEST REQUIREMENTS
--------------------------------------------------

For every moved component:


- update imports
- update tests
- keep behavior unchanged


Add architecture tests if possible.

Validate:

- no forbidden imports
- no cross-domain leakage


--------------------------------------------------
DOCUMENTATION
--------------------------------------------------

Create/update:


docs/architecture/code-ownership-map.md


docs/architecture/context-boundaries.md


docs/architecture/dependency-rules.md


docs/architecture/folder-structure.md


docs/migrations/code-reorganization.md


docs/testing/architecture-tests.md


docs/adr/004-code-ownership-refactoring.md



--------------------------------------------------
OUTPUT
--------------------------------------------------

Generate:

1. Complete file ownership analysis

2. Target location for every moved module

3. Migration sequence

4. Dependency changes

5. Import migration strategy

6. Testing strategy

7. Documentation updates

8. Acceptance criteria


The final backend must have clear ownership boundaries.

Every file must belong to:

- a bounded context
- a layer
- a responsibility

No business logic should remain in generic folders.


- at the end update docs completely to represent the state of project thoroughly.
