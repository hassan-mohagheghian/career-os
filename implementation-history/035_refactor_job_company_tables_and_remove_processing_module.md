# Sprint 14 — Eliminate the Processing Module and Unify Job & Company Lifecycles

## ROLE

You are a Principal Software Architect, DDD Expert, Database Architect, FastAPI Expert, Frontend Architect, and LangGraph Expert.

Your task is to redesign the entire Job and Company lifecycle architecture.

This sprint removes the current Processing bounded context and distributes its responsibilities back into the Job and Company bounded contexts.

Business behavior should remain unchanged.

The implementation may be completely redesigned.

--------------------------------------------------
CURRENT PROBLEM
--------------------------------------------------

The system currently contains a Processing module.

Processing owns part of the lifecycle of both:

- Jobs
- Companies

This creates duplicated concepts, duplicated APIs, duplicated repositories and unclear ownership.

The lifecycle belongs to the domain itself.

Therefore:

Processing should no longer exist as an independent bounded context.

--------------------------------------------------
OBJECTIVES
--------------------------------------------------

Remove the Processing bounded context.

Move all processing responsibilities into:

Job

Company

Each bounded context becomes responsible for its own lifecycle.

--------------------------------------------------
DATABASE REDESIGN
--------------------------------------------------

Review the complete schema.

Remove lifecycle-specific tables.

Examples:

pending_jobs

queued_jobs

processing_jobs

processed_jobs

failed_jobs

These should NOT exist.

Instead:

One Jobs table

One Companies table

Each row owns its current lifecycle status.

Example:

Job

id

title

...

status

Company

id

...

status

The status field becomes the single source of truth.

--------------------------------------------------
JOB STATUS

Design explicit lifecycle states.

Examples:

PENDING

QUEUED

PROCESSING

COMPLETED

FAILED

Status transitions must be deterministic.

--------------------------------------------------
QUEUE MANAGEMENT

When a user starts processing:

The item first enters QUEUED.

It NEVER enters PROCESSING directly.

The scheduler decides when processing begins.

--------------------------------------------------
PROCESSING LIMIT

At most TWO Jobs may be processing simultaneously.

Likewise:

At most TWO Companies may be processing simultaneously.

If the limit is reached:

New items remain in QUEUED.

Whenever a running workflow finishes:

The oldest queued item automatically moves into PROCESSING.

This scheduling behavior must be automatic.

--------------------------------------------------
CANCELLATION

If a queued item is cancelled:

Return it to:

PENDING

If a running workflow is cancelled:

Stop execution gracefully.

Return status according to business rules.

--------------------------------------------------
FAILURE

Workflow failures move the item to:

FAILED

Include:

Failure Reason

Workflow Step

Retry Count

Timestamp

--------------------------------------------------
LANGGRAPH

Workflow state remains inside LangGraph.

Business Status remains inside Job / Company.

Do not mix Workflow State with Business Status.

--------------------------------------------------
ARQ

Workers execute queued items.

Workers update Job / Company status.

Workers never contain business logic.

--------------------------------------------------
FRONTEND

Review the entire UI.

Pages become views over Status.

Pending Page

status == PENDING

Queue Page

status == QUEUED

Processing Page

status == PROCESSING

Processed Page

status == COMPLETED

Failed Page

status == FAILED

Browser refresh must restore the correct state.

--------------------------------------------------
WEBSOCKET

Every status transition emits an event.

Examples:

Queued

Processing Started

Progress Updated

Completed

Failed

Cancelled

Frontend updates immediately.

No polling.

--------------------------------------------------
API REFACTOR

Review every API.

Create consistent REST naming.

Avoid processing-specific endpoints.

Job APIs manage Job lifecycle.

Company APIs manage Company lifecycle.

Use consistent endpoint naming.

Review:

Routes

DTOs

Schemas

Naming

HTTP verbs

Status codes

--------------------------------------------------
MODULE REFACTOR

Remove Processing module.

Move:

Repositories

Models

Services

Application Services

Events

Workers

Validators

Commands

Queries

into:

Job

Company

where they belong.

--------------------------------------------------
DOMAIN EVENTS

Introduce events such as:

JobQueued

JobProcessingStarted

JobCompleted

JobFailed

CompanyQueued

CompanyProcessingStarted

CompanyCompleted

CompanyFailed

Use these events to update WebSockets.

--------------------------------------------------
DATABASE MIGRATION

Create Alembic migrations.

Preserve all existing data.

Avoid destructive migrations.

--------------------------------------------------
TESTING

Create integration tests covering:

Status transitions

Queue scheduling

Processing limit (maximum two concurrent Jobs)

Processing limit (maximum two concurrent Companies)

Automatic dequeue

Failure

Cancellation

Browser refresh

WebSocket synchronization

Database migration

--------------------------------------------------
DOCUMENTATION

Create:

docs/job-lifecycle.md

docs/company-lifecycle.md

docs/status-machine.md

docs/queue-scheduler.md

docs/websocket-events.md

docs/architecture/domain-lifecycle.md

docs/adr/014-remove-processing-bounded-context.md

--------------------------------------------------
ACCEPTANCE CRITERIA

✔ Processing bounded context is removed.

✔ Job owns its lifecycle.

✔ Company owns its lifecycle.

✔ Only one Jobs table exists.

✔ Only one Companies table exists.

✔ Lifecycle is represented by Status.

✔ Queue scheduling enforces a maximum of two concurrent processing tasks.

✔ Status changes are synchronized through WebSockets.

✔ Frontend renders entirely from Status.

✔ API naming is consistent.

✔ Existing functionality is preserved while the architecture becomes simpler and more maintainable.
