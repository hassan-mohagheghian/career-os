# ADR-016: Next.js + Feature-Sliced Design Migration

## Status

Accepted

## Context

The frontend was built as a Vite-based SPA with:
- Hash-based routing
- Manual `fetch()` calls with useState management
- Feature-based organization (not strict FSD)
- No server-state caching

As the application grew, this architecture showed limitations in scalability, maintainability, and developer experience.

## Decision

Migrate to:
1. **Next.js App Router** — file-based routing, SSR/SSG, streaming, layouts
2. **Feature-Sliced Design** — strict layer separation with unidirectional dependencies
3. **TanStack Query** — server-state caching, automatic refetching, mutations

## Migration Strategy

1. Set up Next.js alongside existing Vite project
2. Create FSD layer structure (app/, entities/, features/, widgets/, shared/)
3. Add TanStack Query provider and entity-level hooks
4. Migrate pages to app/ directory
5. Legacy components remain functional via dynamic imports
6. Gradually refactor components to use TanStack Query

## Consequences

### Positive
- Improved scalability with clear layer boundaries
- Type-safe API layer with TanStack Query
- Better developer experience with file-based routing
- Static generation for fast page loads
- Real-time updates maintained via Socket.IO

### Negative
- Migration requires maintaining both old and new code temporarily
- Legacy code has type errors that are suppressed during build
- Some components still use manual fetch() calls (to be refactored)

## Future Work

- Eliminate all manual fetch() calls in favor of TanStack Query
- Add comprehensive test coverage for new architecture
- Improve Server Component usage where possible
