# Sprint 18 — Refactor Background Processing Architecture using ARQ + Redis + Shared Server Infrastructure

## ROLE

You are a Principal Software Architect, Distributed Systems Architect, FastAPI Expert, SQLAlchemy Expert, DDD Expert, LangGraph Expert, ARQ Expert, DevOps Engineer, and Python Infrastructure Engineer.

Your task is to redesign the project's asynchronous execution architecture.

The project currently executes long-running AI workflows inside the Backend.

Those workflows must be migrated into a dedicated Background application powered by ARQ and Redis.

The refactor must preserve every existing business behavior while improving scalability, maintainability, and deployment flexibility.

---

# CURRENT ARCHITECTURE

The project currently contains:

app/

    frontend/

    server/

The frontend has already been migrated to Next.js.

The backend follows Domain-Driven Design.

Business logic is organized into bounded contexts.

Examples:

- Job
- Company
- SDK
- Shared
- Infrastructure
- etc.

The project already separates:

- Domain Models
- SQLAlchemy Models
- Database Layer

The SQLAlchemy models already live inside the dedicated database module.

This separation must be preserved.

---

# TARGET ARCHITECTURE

The project becomes:

app/

    frontend/

    server/

    background/

The new Background application is an independent runtime.

It is NOT another bounded context.

It is an execution service.

Responsibilities:

- Queue Workers
- Workflow Execution
- Retry Logic
- Scheduling
- Progress Reporting
- LangGraph Execution
- AI Providers
- Telemetry

Business logic continues to live inside the Server.

---

# BACKGROUND APPLICATION

Create:

app/background/

Suggested structure:

background/

    workers/

    queue/

    scheduler/

    workflows/

    providers/

    telemetry/

    config/

    infrastructure/

    services/

    utils/

    tests/

Worker entrypoints should remain thin.

Workers should only:

- Receive tasks
- Resolve dependencies
- Execute Application Use Cases
- Publish progress
- Handle retries

Workers must never contain business rules.

---

# QUEUE

Use:

- ARQ
- Redis

Backend responsibilities:

- Authentication
- Validation
- Persistence
- Business Rules
- Queue Scheduling

Background responsibilities:

- Workflow execution
- Long-running AI tasks
- Retry
- Progress
- Failure
- Completion

Backend must never execute AI workflows directly.

---

# WORKFLOWS TO MIGRATE

Move every long-running workflow.

Including:

- Job Processing
- Company Processing
- Resume Tailoring
- Cover Letter Generation
- SDK Roadmap Generation
- Every future AI workflow

The execution location changes.

Business behavior must remain identical.

---

# LANGGRAPH

Every workflow must execute inside Background.

Use:

- LangGraph
- LangGraph State Management
- LangGraph Checkpointing

Never create:

- temporary files
- intermediate markdown
- intermediate json

Use native LangGraph state instead.

---

# BUSINESS OWNERSHIP

Background DOES NOT own business logic.

Business rules remain inside Server.

Examples:

Job

Company

Resume

Cover Letter

Roadmap

Skill

User

Background simply executes them.

---

# SHARED APPLICATION LAYER

Review the Server architecture.

Extract reusable Application Services / Use Cases where appropriate.

Both:

HTTP API

and

Background Workers

must invoke the exact same Application layer.

Never duplicate business logic.

Never implement different behavior for Background.

Execution path should become:

HTTP

↓

Application Service

↓

Domain

or

Background Worker

↓

Application Service

↓

Domain

The business logic must exist only once.

---

# DATABASE ARCHITECTURE

The Server remains the owner of the Business Database.

Background should reuse the existing persistence infrastructure.

Do NOT duplicate:

- SQLAlchemy models
- ORM mappings
- Repository implementations
- Domain models
- Database schema

Instead:

Extract reusable persistence modules from Server.

Background imports those shared modules.

---

# SHARED DATABASE INFRASTRUCTURE

Review current persistence.

Extract reusable infrastructure.

Examples:

Database Session Factory

Engine Configuration

SQLAlchemy Base

Repository Base

Transaction Manager

Database Utilities

Alembic Configuration

These should become reusable by:

Server

Background

without duplication.

---

# BACKGROUND DATABASE

Determine whether Background requires its own persistence.

If Background needs execution-specific storage:

Create Background-owned tables ONLY for execution metadata.

Examples:

workflow_executions

worker_tasks

execution_logs

retry_history

execution_checkpoints

queue_metadata

Do NOT duplicate business entities.

---

# BUSINESS TABLES

Business tables remain owned by Server.

Background may:

Read them

Update them

through the shared persistence layer.

Background must never become the owner of:

Jobs

Companies

Skills

Roadmaps

Users

etc.

---

# SQLALCHEMY

Reuse the existing SQLAlchemy architecture.

If Background requires additional models:

Place them inside Background.

Otherwise reuse existing Server infrastructure.

Never duplicate ORM mappings.

---

# REDIS

Redis responsibilities:

Queue

Scheduling

Worker Coordination

Transient execution state

Nothing else.

Business persistence never belongs inside Redis.

---

# STATUS SYNCHRONIZATION

Workflow status changes should remain synchronized.

Examples:

Pending

Queued

Processing

Completed

Failed

Retry

Cancelled

Progress %

Background updates execution.

Backend updates business state.

Frontend receives updates through existing WebSockets.

Browser refresh must always recover the latest state.

---

# DOCKER

Update Docker support.

Docker Compose should start:

Frontend

Backend

Background

Redis

Any additional required services

Configuration should support both:

Development

Production

---

# PROJECT STARTUP

Review startup commands.

Update every launcher.

Ensure developers can easily start:

Frontend

Backend

Background

Redis

If the project uses a Rust launcher instead of shell scripts, update it accordingly.

---

# DEPLOYMENT

Background must be independently deployable.

The architecture must support:

Docker

Docker Compose

Kubernetes

Cloud Run

AWS ECS

Lambda-compatible environments

Avoid assumptions about local execution.

Configuration must be environment-driven.

---

# GITHUB ACTIONS

Update CI.

Automatically provision:

Redis

Database

Background Worker

Run:

Unit Tests

Integration Tests

Worker Tests

Queue Tests

End-to-End Tests

No hidden external dependencies.

---

# OBSERVABILITY

Implement structured logging.

Track:

Workflow ID

Task ID

Worker ID

Execution ID

Queue Latency

Execution Duration

Retry Count

Correlation ID

Current LangGraph Node

Status Changes

Errors

---

# TESTING

Review the complete test suite.

Update existing tests.

Create tests covering:

Queue

Workers

Retry

Redis

LangGraph

Status propagation

Shared persistence

Docker startup

GitHub Actions

Background execution

All tests must pass.

---

# DOCUMENTATION

Update every affected document.

Create:

docs/background-service.md

docs/arq.md

docs/redis.md

docs/background-workflows.md

docs/deployment/background.md

docs/local-development.md

docs/architecture/background.md

docs/adr/018-background-service.md

Document:

Architecture

Execution Flow

Queue Lifecycle

Worker Lifecycle

Deployment

Retry Strategy

Shared Infrastructure

---

# CLEANUP

Remove:

Old background execution

Temporary file generation

Legacy workflow execution

Dead code

Duplicated repositories

Duplicated ORM models

Duplicated persistence code

---

# ACCEPTANCE CRITERIA

✔ app/background exists.

✔ ARQ is the only background execution framework.

✔ Redis powers all queues.

✔ Long-running workflows execute only inside Background.

✔ Backend only validates, persists and schedules work.

✔ HTTP APIs and Background Workers use the exact same Application Services.

✔ Business logic exists only once.

✔ SQLAlchemy infrastructure is shared.

✔ Business entities remain owned by Server.

✔ Background owns only execution metadata.

✔ No duplicated ORM models exist.

✔ Docker Compose starts the complete platform.

✔ GitHub Actions pass.

✔ Documentation is updated.

✔ Existing business behavior is preserved.

✔ The architecture is scalable, maintainable and cloud-ready.
