# Sprint 12 — End-to-End Job Lifecycle Refactor (Backend + AI + Frontend)

## ROLE

You are a Principal Software Architect, FastAPI Expert, LangGraph Expert, LangChain Expert, Full-Stack Architect, DDD Expert, and Frontend Architect.

Your task is to redesign, validate, and refactor the complete Job lifecycle—from the moment a user submits a new Job until it reaches its final state in the UI.

This sprint covers the entire vertical slice:

- Backend
- AI Workflow
- Queue
- State Management
- WebSocket
- Frontend
- API
- Database
- UX

Business behavior should remain the same, but the implementation may be redesigned where necessary.

---

# CONTEXT

The project already uses:

- FastAPI
- SQLAlchemy ORM
- LangChain
- LangGraph
- ARQ
- Redis
- WebSockets
- DDD
- Hexagonal Architecture
- PostgreSQL / SQLite (current database)

LangGraph native State Management must be used.

Temporary files must NOT be used.

No intermediate JSON/TXT/Markdown files may be created.

---

# OBJECTIVE

Completely review and redesign the Job processing pipeline.

The entire lifecycle should be deterministic, observable, resumable, and fully synchronized between Backend and Frontend.

---

# USER FLOW

Current flow:

User submits Job

↓

Job is validated

↓

Job is created

↓

If Auto Processing = OFF

↓

Move to Queue

↓

Wait

↓

User starts processing

↓

ARQ Worker

↓

LangGraph Workflow

↓

Completed

↓

Move to Processed

If processing fails:

↓

Move to Failed

If Auto Processing = ON

↓

Immediately enqueue

↓

Worker

↓

LangGraph

↓

Processed

---

# SINGLE SOURCE OF TRUTH

There must be exactly one authoritative Job Status.

Do not infer status from temporary files.

Do not infer status from queue position.

Do not infer status from frontend state.

Status must come from backend state.

---

# JOB STATES

Review and redesign the state machine.

Example:

CREATED

↓

QUEUED

↓

WAITING

↓

STARTING

↓

FETCHING

↓

ANALYZING

↓

GENERATING

↓

FINALIZING

↓

COMPLETED

or

FAILED

or

CANCELLED

States should be explicit.

Avoid ambiguous boolean flags.

---

# LANGGRAPH

The workflow must expose meaningful execution stages.

Each stage should update workflow state.

The workflow should emit progress events.

Use LangGraph State only.

No temporary files.

---

# BACKGROUND PROCESSING

FastAPI must never execute processing directly.

FastAPI only:

Validate

↓

Create Job

↓

Enqueue ARQ Job

↓

Return immediately

Worker performs everything else.

---

# WEBSOCKET

WebSocket becomes the real-time event channel.

Emit events for:

Job Created

Queued

Worker Started

Current Node

Progress

Current Step

Retry

Failure

Completion

Cancellation

Frontend must never poll.

---

# FRONTEND SYNCHRONIZATION

Frontend should always reflect backend state.

If browser refreshes:

Reload current state

Reconnect WebSocket

Resume listening

Continue displaying current progress

The user should never lose visibility.

---

# UI PAGES

Review every page.

Queue

Processing

Processed

Failed

Cancelled (if supported)

A Job should automatically appear on the correct page according to its current status.

No manual refresh required.

---

# PAGE TRANSITIONS

Transitions should happen automatically.

Example:

Queue

↓

Processing

↓

Processed

or

Queue

↓

Processing

↓

Failed

Animations are optional.

Correctness is mandatory.

---

# API REVIEW

Review every endpoint.

Examples:

Create Job

Get Job

Queue Job

Start Processing

Retry

Cancel

List Queue

List Processing

List Completed

List Failed

Verify:

HTTP semantics

Validation

Error handling

Idempotency

Status codes

---

# LANGGRAPH STATE

Review the workflow.

Ensure:

No temporary files

No duplicated context

State is typed

State is resumable

Checkpointing used only when appropriate

---

# DATABASE

Persist only business state.

Examples:

Job

Generation

Workflow Status

History

Retry Count

Failure Reason

Progress Metadata

Do NOT persist temporary LLM artifacts.

---

# EVENT MODEL

Introduce domain events where appropriate.

Examples:

JobCreated

JobQueued

ProcessingStarted

WorkflowNodeCompleted

GenerationCompleted

GenerationFailed

JobCancelled

These events drive WebSocket updates.

---

# ERROR HANDLING

Failures must include:

Workflow Step

Provider

Exception

Retry Count

Timestamp

Recoverable / Non-Recoverable

---

# OBSERVABILITY

Track:

Execution ID

Workflow ID

ARQ Job ID

Correlation ID

Current Node

Current State

Worker

Duration

Provider

Token Usage (if available)

---

# TESTING

Create integration tests covering:

Create Job

Queue

Auto Processing

Manual Processing

Processing Success

Processing Failure

Refresh Browser

Reconnect WebSocket

Retry

Cancellation

Resume

Workflow Completion

Frontend synchronization

---

# DOCUMENTATION

Create:

docs/job-lifecycle.md

docs/job-state-machine.md

docs/websocket-events.md

docs/workflow-progress.md

docs/frontend-sync.md

docs/architecture/job-processing.md

docs/adr/012-job-lifecycle.md

Document:

Complete lifecycle

State machine

Event model

WebSocket protocol

Recovery

Retry strategy

Frontend synchronization

---

# ACCEPTANCE CRITERIA

✔ Every Job follows one deterministic lifecycle.

✔ LangGraph owns workflow state.

✔ ARQ owns execution.

✔ FastAPI only orchestrates.

✔ WebSocket provides real-time updates.

✔ Browser refresh preserves the current state.

✔ Jobs automatically move between Queue, Processing, Processed, and Failed.

✔ No temporary files exist.

✔ Backend and Frontend remain fully synchronized.

✔ Existing business behavior is preserved while the implementation becomes cleaner, more reliable, and easier to maintain.
