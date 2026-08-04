# Prompt: Implement the New Jobs List Backend API

Your task is to implement **only** the backend APIs required by the new Jobs List.

Do **NOT** implement ProcessingExecution, LangGraph, ARQ workers, SSE, or background processing.

Only implement the APIs required for browsing jobs.

---

# Read These Documents

## Architecture

* docs/architecture/ddd-structure.md
* docs/architecture/hexagonal-architecture.md
* docs/architecture/context-boundaries.md
* docs/feature-sliced-design.md

---

## Domain

* docs/domain/jobs/job-list-item.md
* docs/domain/jobs/job-search.md

---

## API

* docs/api/jobs/list-jobs.md

---

## UX

* docs/ux/features/jobs/page.md
* docs/ux/features/jobs/job-row.md

---

## Database

* docs/database/sqlalchemy-architecture.md

---

# Goal

Implement the new Jobs List API without affecting the legacy API.

The legacy endpoints must continue to work.

The new endpoints should live beside them.

---

# Endpoints

Implement

GET /api/jobs

This endpoint replaces the legacy listing endpoint for the new frontend.

---

# Query Parameters

Support the documented query model.

At minimum:

* page
* page_size
* search
* sort
* order

Filtering support:

* processing_status
* company_id
* company_type
* remote
* visa
* score_range
* fit_score_range
* success_score_range
* overall_score_range

The API should ignore unsupported filters gracefully.

---

# Response Model

Return the new JobListItem DTO described in

docs/domain/jobs/job-list-item.md

Do not return ORM entities directly.

Use dedicated response schemas.

---

# Architecture

Follow DDD and Hexagonal Architecture.

Create proper layers.

Example

Presentation

Application

Domain

Infrastructure

Repository

Mapper

DTO

Do not place SQLAlchemy code inside API routes.

---

# Repository

Create a dedicated repository for listing jobs.

The repository should support:

* pagination
* filtering
* searching
* sorting

Avoid loading unnecessary relationships.

Use efficient SQLAlchemy queries.

---

# Searching

Search across

* title
* company name
* location

Support case-insensitive matching.

---

# Sorting

Support at least

* created_at
* updated_at
* title
* company
* overall_score
* fit_score
* success_score

Unknown sort fields should fall back to updated_at DESC.

---

# Pagination

Return

items

page

page_size

total_items

total_pages

has_next

has_previous

---

# Missing Fields

The database may not yet contain

* overall_score
* fit_score
* success_score
* visa
* remote
* logo

Return null or documented default values.

Do not fabricate data.

The API must remain stable even if fields are unavailable.

---

# Validation

Validate all query parameters.

Return proper HTTP 400 responses for invalid values.

---

# Performance

Avoid N+1 queries.

Use eager loading only where necessary.

Never load large text fields that are not used in the list view.

---

# Testing

Add tests for

* pagination
* search
* sorting
* filtering
* invalid query parameters
* empty result
* default sorting

---

# Backward Compatibility

Do NOT modify

legacy routes

legacy response models

legacy repositories

Everything new must coexist with the existing implementation.

---

# Deliverables

Implement

* GET /api/jobs
* Request schemas
* Response schemas
* JobListItem DTO
* Search model
* Repository
* Service/Application layer
* Mapping layer
* Tests

Do NOT implement

* ProcessingExecution
* Process Job endpoint
* ARQ
* LangGraph
* SSE
* Queue management
* Background workers

Focus only on providing a production-ready Jobs List API for the new frontend.
