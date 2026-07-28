# ADR-009: AI Tool Platform — Local-First Tool Execution

## Status

Accepted

## Context

The codebase had 4+ duplicated `_fetch_url` functions across different files, each implementing the same HTTP fetch + HTML cleaning logic. LLM workflows were tightly coupled to specific providers, and there was no caching, no structured outputs, and no observability for tool executions.

## Decision

Implement a unified AI Tool Layer that:

1. **Consolidates all URL fetching** into a single `fetch_page()` function
2. **Follows local-first philosophy**: Always prefer local execution over provider tools
3. **Provides structured outputs**: `FetchedPage` model with typed fields
4. **Adds caching**: File-based cache with configurable TTL
5. **Implements tool registry**: Priority-based tool selection
6. **Ensures provider independence**: No provider-specific logic in workflows

## Consequences

### Positive

- **4x code reduction**: One `_fetch_url` instead of 4 duplicated copies
- **Lower latency**: Local HTTP is faster than LLM provider tools
- **Lower cost**: No tokens consumed for URL fetching
- **Deterministic**: Same URL always returns same content
- **Cached**: Redundant fetches are avoided (6h TTL)
- **Observable**: All tool executions logged with timing
- **Testable**: 46 new tests covering the complete tool layer
- **Provider-independent**: Easy to add new providers without modifying workflows

### Negative

- **New dependency**: `pydantic` for structured models (already in project)
- **Cache management**: Need to handle cache invalidation
- **Learning curve**: Developers need to understand the tool layer

### Neutral

- **Migration effort**: Updated 8 files to use the new tool layer
- **Test coverage**: All 1253 existing tests continue to pass

## Alternatives Considered

### 1. Keep Duplicated Functions

- **Pros**: No change needed
- **Cons**: Continued code duplication, no caching, no observability

### 2. Use Provider-Native Tools

- **Pros**: Less code to maintain
- **Cons**: Higher cost, higher latency, provider lock-in, non-deterministic

### 3. Use Third-Party Fetch Library (e.g., httpx + BeautifulSoup)

- **Pros**: More features (async, better parsing)
- **Cons**: New dependency, overkill for current use case

## References

- `docs/ai/tooling.md` — Tool layer overview
- `docs/ai/web-fetching.md` — Web fetching pipeline
- `docs/ai/tool-selection.md` — Tool selection strategy
- `docs/architecture/tool-layer.md` — Architecture details
- `app/server/ai/infrastructure/tools/` — Implementation
