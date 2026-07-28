# Shared Kernel

## Purpose

The shared kernel contains concepts that are truly shared across all bounded contexts. It is the foundation that every context depends on.

## Contents

### Domain Primitives
- `BaseEntity` — Identity management (id, created_at, updated_at)
- `ValueObject` — Immutable value types with equality by value
- `DomainEvent` — Base class for domain events
- `RepositoryInterface` — Base ABC for repository contracts

### Application Layer
- `AppError` hierarchy — Consistent error handling (NotFoundError, ValidationError, etc.)
- `DTO` / `PaginationDTO` — Data transfer object base classes

### Infrastructure
- `get_session` / `get_session_sync` — SQLAlchemy session factories
- Logging configuration
- WebSocket broadcaster

### Presentation
- `app_error_handler` — FastAPI exception handler

## Rules

1. **Minimal footprint** — Only truly shared concepts belong here
2. **No business logic** — Shared kernel has no domain-specific rules
3. **Stable API** — Changes affect all contexts, so changes are rare
4. **No dependencies on contexts** — Shared kernel never imports from bounded contexts

## Anti-Patterns to Avoid

- Don't put utility functions here ("common" folder smell)
- Don't put business entities here (they belong in their context)
- Don't put framework-specific code here (keep it abstract)
