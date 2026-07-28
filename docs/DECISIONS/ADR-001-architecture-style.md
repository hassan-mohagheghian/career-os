# ADR-001: Architecture Style

## Context

Need a web application architecture for a career intelligence platform that handles job processing, company analysis, skill management, and AI-powered insights.

## Decision

Monolithic Flask backend + React SPA frontend + SQLite database + Mimo CLI subprocess for AI.

## Alternatives

- **Microservices**: Rejected — single developer project, too much operational overhead
- **Next.js**: Rejected — user explicitly wanted Flask + React/Vite, not Next.js
- **PostgreSQL**: Rejected — SQLite is simpler, sufficient for single-user, no server needed
- **Django**: Rejected — Flask is lighter weight, better fit for API-only backend

## Consequences

**Positive:**
- Simple deployment (single `./start`)
- No external database server needed
- Easy to understand and modify
- Fast development iteration

**Negative:**
- SQLite limitations (concurrent writes, no full-text search)
- Single process limits scalability
- No built-in authentication/authorization
