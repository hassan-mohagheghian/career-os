# Task: Implement ProcessingExecution Backend

## Goal
im
* Queue UI

This task is only responsible for introducing the new Processing bounded context and the ProcessingExecution domain model.

---

## Read These Documents First

Read and follow these documents before making any changes.

### Architecture

* docs/architecture/ARCHITECTURE.md
* docs/architecture/ddd-structure.md
* docs/architecture/hexagonal-architecture.md
* docs/architecture/dependency-rules.md
* docs/architecture/context-boundaries.md
* docs/architecture/shared-kernel.md

### Domain

* docs/domain/processing/processing-execution.md
* docs/domain/processing/events.md

### Feature

* docs/features/job-processing.md

### API

* docs/api/processing/process-job.md

### Development

* docs/database/sqlalchemy-architecture.md
* docs/database/alembic-guide.md

---

## Requirements

Implement the Processing bounded context.

The bounded context must contain:

* Domain
* Application
* Infrastructure
* API

following the project's DDD and Hexagonal Architecture.

---

## Implement

### Domain

Implement:

* ProcessingExecution entity
* ExecutionStatus enum
* ExecutionType enum

Follow the documentation exactly.

Use UUIDv7.


### ExecutionType

Implement ExecutionType as an enum.

Initial values:

- JOB_PROCESSING
- COMPANY_PROCESSING
- COVER_LETTER_GENERATION
- RESUME_GENERATION
- RESUME_OPTIMIZATION
- COMPANY_ANALYSIS
- MARKET_ANALYSIS
- CAREER_INSIGHTS

The current implementation must support only:

- JOB_PROCESSING

The remaining values are reserved for future features.

Do not implement any logic for them.

The enum exists only to make the ProcessingExecution infrastructure reusable.

### ExecutionStatus

Implement ExecutionStatus as an enum.

Values:

- CREATED
- QUEUED
- STARTING
- RUNNING
- COMPLETED
- FAILED
- CANCELLED

No additional statuses should be introduced.


### ProcessingExecution

ProcessingExecution must be generic.

It must not contain any Job-specific business logic.

The entity should reference:

- execution_type
- target_type
- target_id

rather than directly referencing a Job.

This allows the same infrastructure to process future entities without schema changes.


---

### Persistence

Create the ProcessingExecution database model.

Use:

* SQLAlchemy ORM
* PostgreSQL
* Alembic migration

Do not use raw SQL.

---

### Repository

Create a repository interface.

Create a SQLAlchemy implementation.

---

### Application Layer

Implement the following use case:

CreateProcessingExecution

Responsibilities:

* Validate input
* Create ProcessingExecution
* Persist entity
* Return execution id

Nothing else.

---

### API

Implement

POST

/jobs/{jobId}/process

Current behavior:

* validate job
* create ProcessingExecution
* return HTTP 202

Do NOT enqueue anything.

Do NOT execute anything.

Do NOT call LangChain.

Do NOT call ARQ.

---

## Events

Define Processing domain events.

Only define the domain events.

Do NOT publish them.

---

## Testing

Create:

* domain tests
* repository tests
* API tests

Follow the project's testing strategy.

---

## Constraints

Do NOT modify existing job processing.

Do NOT remove legacy processing.

Do NOT change the existing Process button.

Do NOT introduce background workers.

Do NOT implement queue logic.

Do NOT implement SSE.

Do NOT implement LangGraph.

---

## Deliverables

At the end of this task the project must contain:

* Processing bounded context
* ProcessingExecution entity
* Repository
* Database migration
* CreateProcessingExecution use case
* REST endpoint
* Tests

Nothing else.

If any subsequent feature depends on ARQ, LangGraph, SSE, or AI execution, leave clear TODO markers instead of implementing them.
