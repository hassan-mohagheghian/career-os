# ROLE

You are a Principal Software Architect and Senior Python Backend Engineer.

You specialize in production-scale migrations from Flask to FastAPI, Clean Architecture, DDD, and AI-native backend systems.

Your task is to design and plan a safe architectural migration.

This is NOT a rewrite.

This is NOT a feature development task.

This is a controlled migration while preserving existing behavior.


--------------------------------------------------
PROJECT CONTEXT
--------------------------------------------------

Use the following existing project context:

[PASTE CURRENT PROJECT CONTEXT HERE]


--------------------------------------------------
CURRENT SYSTEM
--------------------------------------------------

Current architecture:

Frontend:
- React 18
- TypeScript
- Vite
- shadcn/ui
- Tailwind CSS

Backend:
- Flask 3.1
- Flask Blueprint architecture
- Flask-SocketIO
- Python 3.14+
- Service layer
- Raw SQL database access

Database:
- SQLite
- Existing tables and migration system

AI:
- LLMService abstraction
- LangChain
- LangGraph
- Mimo provider
- Existing AI workflows


--------------------------------------------------
MAIN OBJECTIVE
--------------------------------------------------

Migrate the backend architecture from Flask to FastAPI.

The migration must:

- preserve current functionality
- preserve API behavior
- preserve existing business rules
- minimize risk
- create a foundation for future evolution


--------------------------------------------------
IMPORTANT CONSTRAINTS
--------------------------------------------------

Do NOT:

- migrate database to PostgreSQL yet
- introduce ORM
- redesign existing features
- create Graph Engine
- change frontend architecture
- rewrite AI architecture
- remove existing functionality


--------------------------------------------------
TARGET STACK
--------------------------------------------------

The future backend foundation should use:

FastAPI

Pydantic v2

Uvicorn

SQLAlchemy Core compatibility

Alembic compatibility

PostgreSQL compatibility

structlog

pytest


--------------------------------------------------
ARCHITECTURE REQUIREMENTS
--------------------------------------------------

Design a production-grade backend architecture based on:

- Clean Architecture
- Domain Driven Design
- SOLID principles
- Feature-based organization
- Dependency Injection
- Repository Pattern
- Service Layer


The architecture should contain clear boundaries between:

Presentation Layer

Application Layer

Domain Layer

Infrastructure Layer

Shared/Core Layer


--------------------------------------------------
FOLDER STRUCTURE
--------------------------------------------------

Design the recommended FastAPI folder structure.

Explain responsibilities for:

app/

api/

core/

domain/

application/

infrastructure/

features/

repositories/

services/

events/

workers/

tests/


The structure must support future modules:

- Jobs Intelligence
- Company Intelligence
- Skills Graph
- Roadmap Engine
- AI Agents
- Recommendation Engine


--------------------------------------------------
API MIGRATION
--------------------------------------------------

Design the migration from Flask Blueprints to FastAPI Routers.

Define:

- router organization
- API versioning
- request validation
- response schemas
- error handling
- dependency injection


--------------------------------------------------
DEPENDENCY INJECTION
--------------------------------------------------

Create a scalable dependency injection strategy.

The design must support:

- database connection
- repositories
- services
- AI clients
- configuration
- authentication


Avoid:

- global mutable state
- hidden dependencies


--------------------------------------------------
CONFIGURATION MANAGEMENT
--------------------------------------------------

Design configuration management.

Support:

- development environment
- production environment
- testing environment
- environment variables
- secrets management


--------------------------------------------------
LOGGING
--------------------------------------------------

Keep structlog.

Design a centralized logging strategy.

Include:

- request logging
- error logging
- AI workflow logging
- background task logging


--------------------------------------------------
WEBSOCKET MIGRATION
--------------------------------------------------

Analyze the existing Flask-SocketIO usage.

Design the FastAPI-compatible solution.

Explain:

- WebSocket architecture
- connection management
- event handling
- real-time progress updates


--------------------------------------------------
BACKGROUND TASKS
--------------------------------------------------

Design the background processing architecture.

Consider:

- AI generation jobs
- document processing
- company analysis
- job extraction

Do not introduce unnecessary infrastructure.

--------------------------------------------------
TESTING STRATEGY
--------------------------------------------------

Design testing strategy:

- unit tests
- service tests
- API tests
- integration tests
- migration tests


--------------------------------------------------
MIGRATION PLAN
--------------------------------------------------

Create a safe migration roadmap.

Include:

Phase 1:
Preparation

Phase 2:
FastAPI foundation

Phase 3:
Feature migration

Phase 4:
Flask removal


For each phase define:

- tasks
- risks
- validation criteria


--------------------------------------------------
DOCUMENTATION REQUIREMENTS
--------------------------------------------------

Generate documentation updates.

The following documents must be created or updated:


docs/architecture/backend-architecture.md

Content:
- backend layers
- responsibilities
- request flow


docs/architecture/backend-structure.md

Content:
- folder structure
- module boundaries


docs/architecture/dependency-injection.md

Content:
- dependency strategy


docs/api/api-design.md

Content:
- API conventions
- versioning
- error handling


docs/migrations/flask-to-fastapi.md

Content:
- migration steps
- rollback strategy


docs/testing/backend-testing.md

Content:
- testing approach


docs/adr/001-fastapi-migration.md

Content:
- decision
- alternatives
- reasons


--------------------------------------------------
OUTPUT FORMAT
--------------------------------------------------

Produce a complete engineering proposal.

Include:

1. Executive Summary

2. Current Architecture Analysis

3. Target FastAPI Architecture

4. Folder Structure

5. API Migration Strategy

6. Dependency Injection Design

7. WebSocket Strategy

8. Background Processing Strategy

9. Testing Strategy

10. Migration Plan

11. Documentation Plan

12. Risks and Mitigation

13. Acceptance Criteria

14. Implementation Checklist


The result must be implementation-ready for a senior engineering team.
