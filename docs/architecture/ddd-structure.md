# DDD Structure

## Overview

The backend follows Domain-Driven Design principles organized as a modular monolith.

## Bounded Contexts

Each bounded context is a Python package under `app/server/`:

```
<context>/
├── domain/           # Pure business concepts
│   ├── entities/     # Aggregate roots and entities
│   ├── value_objects/ # Immutable value types
│   └── repositories/ # Data access interfaces (ABCs)
├── application/      # Use cases and orchestration
│   ├── use_cases/    # Single-purpose operations
│   └── dto/          # Data transfer objects
├── infrastructure/   # External integrations
│   ├── models/       # SQLAlchemy ORM models
│   ├── repositories/ # Repository implementations
│   └── workers/      # Background processing
└── presentation/     # External interfaces
    ├── api/          # FastAPI routers
    └── schemas/      # Pydantic request/response schemas
```

## Rules

1. **Domain layer** depends on nothing (except shared kernel)
2. **Application layer** depends only on domain
3. **Infrastructure layer** implements domain interfaces
4. **Presentation layer** depends only on application layer
5. Cross-context communication goes through application layer or domain events

## Import Convention

```python
# Within a context
from jobs.domain.entities.job import Job
from jobs.infrastructure import SQLAlchemyJobRepository

# Cross-context (via shared kernel)
from shared.domain.entity import BaseEntity
from shared.application.exceptions import NotFoundError
```
