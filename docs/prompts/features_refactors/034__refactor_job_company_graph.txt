# Sprint 13 — Unify Job & Company Processing Pipelines

## ROLE

You are a Principal Software Architect, DDD Expert, Database Architect, FastAPI Expert, LangGraph Expert, Full-Stack Architect, and Systems Designer.

Your task is to redesign the entire processing pipeline for Jobs and Companies.

Both domains currently implement nearly identical concepts independently.

The goal is to create a single architectural pattern while preserving domain boundaries.

Business behavior must remain unchanged.

--------------------------------------------------
CONTEXT
--------------------------------------------------

The project already uses:

- FastAPI
- SQLAlchemy ORM
- LangGraph
- LangChain
- ARQ
- Redis
- DDD
- Hexagonal Architecture

Both Job and Company currently have independent processing pipelines.

These implementations have diverged and contain duplicated logic.

--------------------------------------------------
OBJECTIVE
--------------------------------------------------

Review the complete lifecycle of both:

- Job Processing
- Company Processing

Compare them.

Identify duplicated concepts.

Create one unified processing architecture.

Do NOT merge the domains.

Instead, standardize the pipeline pattern.

--------------------------------------------------
CURRENT FLOW
--------------------------------------------------

Jobs

Pending

↓

Queued

↓

Processing

↓

Processed

or

Failed

Companies

Pending

↓

Queued

↓

Processing

↓

Processed

or

Failed

These two pipelines should follow the same architecture.

--------------------------------------------------
DATABASE REVIEW
--------------------------------------------------

Inspect all processing-related tables.

Examples:

Pending tables

Queue tables

Processed tables

Failed tables

History tables

Determine whether multiple tables exist only because of status differences.

If so:

Refactor into a single aggregate table per bounded context.

Example:

Job

status

instead of:

pending_jobs

processed_jobs

failed_jobs

Likewise:

Company

status

instead of multiple lifecycle tables.

Use explicit status fields instead of physically moving rows between tables.

--------------------------------------------------
STATE MACHINE
--------------------------------------------------

Design explicit lifecycle states.

Example:

CREATED

↓

PENDING

↓

QUEUED

↓

PROCESSING

↓

COMPLETED

or

FAILED

or

CANCELLED

Transitions should be deterministic.

--------------------------------------------------
PIPELINE ARCHITECTURE
--------------------------------------------------

Design one generic processing pipeline abstraction.

Examples:

Validation

Queue

Worker

Workflow

Persistence

Events

Completion

Failure

Jobs and Companies should both use this architecture.

Only domain-specific logic should differ.

--------------------------------------------------
SHARED COMPONENTS
--------------------------------------------------

Extract reusable infrastructure.

Examples:

Queue Management

Status Updates

Retry Logic

Worker Dispatch

Workflow Execution

Progress Tracking

Failure Handling

Completion Handling

Avoid duplicated implementations.

--------------------------------------------------
FRONTEND

Review the entire UI.

Pages should derive their content from status.

Example:

Pending Page

shows

status == PENDING

Queue Page

shows

status == QUEUED

Processing Page

shows

status == PROCESSING

Processed Page

shows

status == COMPLETED

Failed Page

shows

status == FAILED

Frontend must never infer state.

Backend is the source of truth.

--------------------------------------------------
WEBSOCKET

Every state transition must emit an event.

Examples:

Queued

Started

Progress

Completed

Failed

Cancelled

Frontend updates automatically.

Browser refresh should restore the correct state.

--------------------------------------------------
LANGGRAPH

Workflow execution should update the unified status model.

Workflow progress should remain independent from business entities.

Workflow State is not Job Status.

Workflow execution updates Job Status.

--------------------------------------------------
ARQ

Workers execute pipeline stages.

Workers never contain business logic.

Workers only orchestrate execution.

--------------------------------------------------
API REVIEW

Review every endpoint.

Ensure consistent behavior across Jobs and Companies.

Examples:

Create

Queue

Retry

Cancel

Get Status

List by Status

Keep endpoint semantics consistent.

--------------------------------------------------
DATABASE MIGRATION

If schema changes are necessary:

Create Alembic migrations.

Preserve existing data.

Avoid destructive migrations.

--------------------------------------------------
TESTING

Create integration tests covering:

Job lifecycle

Company lifecycle

Queue transitions

Processing

Completion

Failure

Retry

Cancellation

Frontend synchronization

Database migrations

--------------------------------------------------
DOCUMENTATION

Create:

docs/processing-pipeline.md

docs/job-pipeline.md

docs/company-pipeline.md

docs/state-machine.md

docs/frontend-status.md

docs/architecture/unified-processing.md

docs/adr/013-unified-processing-pipeline.md

--------------------------------------------------
ACCEPTANCE CRITERIA

✔ Jobs and Companies follow the same processing architecture.

✔ Status is represented by explicit state, not separate tables.

✔ Duplicate infrastructure is eliminated.

✔ Domain logic remains separate.

✔ Backend is the single source of truth.

✔ Frontend renders based solely on status.

✔ WebSocket updates remain synchronized.

✔ LangGraph integrates cleanly with the pipeline.

✔ ARQ orchestrates execution.

✔ Existing functionality is preserved.
