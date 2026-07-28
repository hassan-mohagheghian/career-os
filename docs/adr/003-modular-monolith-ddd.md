# ADR-003: Modular Monolith with DDD

## Status

Accepted

## Context

The Job Search Intelligence platform backend grew organically with mixed concerns across API, service, and infrastructure layers. Domain boundaries were unclear, some business logic lived in API handlers, and infrastructure concerns leaked into business logic. The codebase needed structural improvement without changing runtime behavior.

## Decision

We will refactor the backend into a **DDD-based modular monolith** with:

1. **Bounded Contexts** — Jobs, Companies, Skills, Career, Resume, AI, Pending, Shared
2. **Layered Architecture** per context — domain, application, infrastructure, presentation
3. **Shared Kernel** — base entities, value objects, exceptions, session management
4. **Repository Pattern** — domain defines interfaces, infrastructure implements them
5. **Hexagonal Architecture** — domain at center, no outward dependencies

## Consequences

### Positive
- Clear separation of concerns per bounded context
- Domain logic is testable in isolation (no DB, no HTTP)
- Each context can be extracted to a microservice independently
- New developers can navigate code by context, not by technical layer
- Database schema remains unchanged (SQLite preserved)

### Negative
- More files and directories to navigate
- Import paths are longer
- Migration requires updating many files at once
- Some duplication in re-export wrappers during transition

### Risks
- Over-engineering for a small team — mitigated by keeping contexts simple
- Performance overhead from abstraction layers — negligible for this use case

## Alternatives Considered

1. **Flat module structure** — rejected, doesn't scale
2. **Microservices from day one** — rejected, premature for current scale
3. **Domain Events everywhere** — deferred to future extraction phase

## References

- `docs/architecture/bounded-context-analysis.md`
- `docs/architecture/modular-monolith.md`
