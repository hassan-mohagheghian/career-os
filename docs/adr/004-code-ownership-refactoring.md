# ADR-004: Code Ownership Refactoring to DDD

## Status

Accepted

## Context

The codebase had grown organically with technical-layer-based organization:
- `api/v1/` contained all API routers
- `schemas/` contained all Pydantic schemas  
- `services/` contained all business logic
- `core/` contained database and queue code
- `scripts/` contained standalone scripts
- `prompts/` contained all AI prompts

This made it unclear which team/module owned which code, and created
tight coupling between unrelated business capabilities.

## Decision

Refactor to Domain-Driven Design (DDD) with bounded contexts:

1. **Jobs** — Job posting lifecycle
2. **Companies** — Company intelligence
3. **Skills** — Skill management, aliases, relationships
4. **Rules** — Scoring rules (was Career)
5. **Resume** — Resume/cover letter generation
6. **Pending** — Processing queue management
7. **Shared** — Cross-cutting infrastructure

Each bounded context owns its complete vertical slice:
- `domain/` — Entities, value objects, repository interfaces
- `application/` — Use cases, services, DTOs
- `infrastructure/` — Models, repository implementations, workers, AI prompts
- `presentation/` — API routers, schemas, CLI commands

## Consequences

### Positive
- Clear code ownership per business capability
- Independent development of each context
- Enforced dependency direction (presentation → application → domain)
- Easier onboarding — new developers can focus on one context
- Better testability — each context can be tested in isolation

### Negative
- More directories to navigate
- Import paths are longer
- Need backward-compatible re-exports during migration
- Initial refactoring effort is significant

### Mitigations
- Backward-compatible re-export shims at old locations
- Gradual migration — existing code continues to work
- Architecture documentation for navigation
- Lazy imports in `__init__.py` to prevent circular dependencies

## Alternatives Considered

1. **Feature-based organization** — Rejected because features span multiple business capabilities
2. **Hexagonal architecture only** — Rejected because it doesn't enforce business boundary ownership
3. **Microservices** — Rejected because the project is a monolith with shared database

## References

- Domain-Driven Design (Eric Evans)
- Clean Architecture (Robert C. Martin)
- Hexagonal Architecture (Alistair Cockburn)
