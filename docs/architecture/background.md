# Background Architecture

## Overview

The background service is a separate Python application that runs ARQ workers for executing long-running AI workflows. It shares the database with the server but is independently deployable.

## Flow

```
Client → FastAPI (Server)
            │
            │ Validate, persist, enqueue
            ▼
         Redis Queue
            │
            │ Dequeue
            ▼
         ARQ Worker (Background)
            │
            │ Execute workflow
            ▼
         Application Services
            │
            │ Read/write
            ▼
         Shared Database
```

## Separation of Concerns

| Layer | Server | Background |
|---|---|---|
| Authentication | ✓ | |
| Validation | ✓ | |
| Persistence | ✓ | |
| Business Rules | ✓ | |
| Queue Scheduling | ✓ | |
| Workflow Execution | | ✓ |
| Long-running AI Tasks | | ✓ |
| Retry | | ✓ |
| Progress Reporting | | ✓ |

## Shared Infrastructure

- SQLAlchemy engine, session factory, Base class
- Repository implementations
- Domain models and ORM mappings
- Application services and use cases

Business logic lives exactly once — in the Server. Background only executes it.
