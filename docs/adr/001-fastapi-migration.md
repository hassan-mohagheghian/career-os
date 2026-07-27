# ADR-001: Migrate from Flask to FastAPI

## Status

Accepted (Completed)

## Context

The Job Search Intelligence platform currently uses Flask 3.1 as its backend framework. As the platform evolves toward supporting multiple concurrent users, real-time features, and future PostgreSQL migration, the team has identified several limitations with the current Flask setup:

### Current Limitations

1. **No native async support** — Flask runs synchronously, limiting I/O-bound operations
2. **Global mutable state** — Flask app, SocketIO, database connections are module-level globals
3. **No type safety** — Request/response validation is manual
4. **Limited WebSocket support** — Flask-SocketIO is a wrapper, not native
5. **Thread-based concurrency** — Background tasks use `threading.Thread`, not async
6. **No dependency injection** — Services access globals directly

### Business Requirements

- Preserve all existing functionality during migration
- Maintain API compatibility for frontend
- Enable future PostgreSQL migration
- Support real-time progress updates
- Improve code maintainability
- Enable better testing patterns

## Decision

Migrate the backend from Flask to FastAPI while preserving all existing behavior.

## Alternatives Considered

### 1. Stay with Flask

**Pros:**
- No migration effort
- Team familiarity
- Stable ecosystem

**Cons:**
- No native async (limits future scalability)
- Global state makes testing harder
- Flask-SocketIO is a wrapper, not native
- No built-in type validation
- Flask ecosystem moving slower than FastAPI

**Verdict:** Rejected — doesn't address identified limitations

### 2. Migrate to Django

**Pros:**
- Built-in ORM (future PostgreSQL support)
- Built-in admin interface
- Strong ecosystem
- Built-in authentication

**Cons:**
- Heavier framework (overkill for API-only backend)
- ORM adds complexity we don't need yet
- Migration effort similar to FastAPI
- Less modern async support
- More opinionated structure

**Verdict:** Rejected — too heavy for current needs

### 3. Migrate to FastAPI

**Pros:**
- Native async/await
- Built-in type validation (Pydantic v2)
- Native WebSocket support
- Dependency injection built-in
- Modern, fast-growing ecosystem
- Easy to migrate incrementally
- Compatible with future PostgreSQL/ORM

**Cons:**
- Migration effort required
- Team needs to learn new patterns
- Less mature than Flask/Django

**Verdict:** Accepted — best fit for requirements

### 4. Migrate to Litestar

**Pros:**
- Similar to FastAPI
- Built-in DI container
- Better OpenAPI support

**Cons:**
- Smaller ecosystem
- Less community support
- Migration effort similar to FastAPI

**Verdict:** Rejected — FastAPI has larger ecosystem and community

## Consequences

### Positive

1. **Native async support** — Better I/O performance for database and API calls
2. **Type safety** — Pydantic v2 models ensure request/response validation
3. **Dependency injection** — Clean, testable architecture
4. **Native WebSocket** — First-class real-time support
5. **Better testing** — Easy to mock dependencies
6. **Future-proof** — Ready for PostgreSQL, ORMs, microservices

### Negative

1. **Migration effort** — 2-3 weeks of development
2. **Learning curve** — Team needs to learn FastAPI patterns
3. **Temporary complexity** — Running Flask and FastAPI side-by-side during migration

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Response format differences | Medium | High | Comparison tests, manual review |
| WebSocket incompatibility | Low | High | Port Broadcaster carefully |
| Background task failures | Medium | Medium | Test with production load |
| Performance regression | Low | Medium | Benchmark before/after |

## Implementation Plan

### Phase 1: Preparation (1-2 days)
- Create FastAPI entry point
- Set up dependency injection
- Create Pydantic models
- Set up test infrastructure

### Phase 2: Foundation (2-3 days)
- Core infrastructure (WebSocket, logging, error handling)
- Database layer (repositories)
- WebSocket support
- Background tasks

### Phase 3: Feature Migration (5-7 days)
- Migrate features one-by-one
- Run comparison tests
- Switch traffic to FastAPI

### Phase 4: Flask Removal (1-2 days)
- Remove Flask code
- Clean up imports
- Update documentation

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

## Related Decisions

- ADR-002: Database Choice (SQLite → PostgreSQL future)
- ADR-003: AI Integration (LLMService abstraction preserved)
- ADR-004: AI Agent Orchestration (LangGraph preserved)
