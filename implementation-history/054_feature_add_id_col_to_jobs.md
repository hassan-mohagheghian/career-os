# Prompt: Introduce UUIDv7 Public IDs for Jobs

The current `jobs` table uses an integer column named `num` as its primary identifier.

This identifier is currently exposed through the legacy APIs.

We want to introduce a new public identifier for all future APIs without breaking backward compatibility.

Do **NOT** remove or rename `num`.

Instead, introduce a new UUIDv7 identifier and migrate the new architecture to use it.

---

# Read These Documents

## Architecture

* docs/architecture/ddd-structure.md
* docs/architecture/hexagonal-architecture.md
* docs/architecture/context-boundaries.md

## Database

* docs/database/sqlalchemy-architecture.md
* docs/migrations/code-reorganization.md

## Domain

* docs/domain/jobs/job-list-item.md
* docs/domain/jobs/job-search.md

## API

* docs/api/jobs/list-jobs.md
* docs/api/jobs/create-job.md

---

# Goal

Introduce a stable public identifier for Jobs.

Legacy APIs continue using `num`.

All new APIs must use `id` (UUIDv7).

---

# Requirements

## 1. Database

Add a new column

```
id UUID
```

Requirements

* UUID Version 7
* NOT NULL
* UNIQUE
* Indexed
* Generated automatically
* Never changes after creation

Do NOT modify

* num
* existing primary key
* existing foreign keys

The migration must be backward compatible.

---

## 2. Data Migration

Write an Alembic migration that

* adds the new column
* generates UUIDv7 values for every existing row
* creates a unique index
* validates there are no NULL values

The migration must be safe for production.

---

## 3. SQLAlchemy Model

Update the Job model.

Expose both

```
num
```

and

```
id
```

`num` remains the internal legacy identifier.

`id` becomes the public identifier.

---

## 4. Domain

All new domain models must use

```
Job.id
```

instead of

```
Job.num
```

The legacy domain can continue using `num`.

---

## 5. DTOs

Every new DTO should expose

```
id
```

Never expose `num` through the new APIs.

Legacy DTOs remain unchanged.

---

## 6. Repository Layer

Repositories used by the new Jobs APIs must query using

```
id
```

Repositories used by legacy endpoints may continue using

```
num
```

---

## 7. API

Every new endpoint should use

```
/jobs/{id}
```

where

```
id = UUIDv7
```

Legacy endpoints remain unchanged.

Example

Legacy

```
GET /legacy/jobs/{num}
```

New

```
GET /api/jobs/{id}
```

---

## 8. Future Compatibility

This UUID will become the canonical identifier for

* ProcessingExecution
* Queue
* LangGraph
* SSE Events
* Recommendations
* Resume matching
* Insights
* AI workflows

Design accordingly.

---

## 9. Frontend Compatibility

The new frontend must use only

```
job.id
```

Never use `num`.

Legacy frontend continues using `num`.

---

## 10. Tests

Add tests verifying

* UUIDv7 generation
* Existing rows receive UUIDs
* UUID uniqueness
* Repository lookup by UUID
* Legacy lookup by num still works

---

# Constraints

Do NOT

* change primary keys
* remove num
* rename num
* break existing endpoints
* break existing migrations

This is an additive migration only.

---

# Deliverables

Implement

* Alembic migration
* SQLAlchemy model update
* UUIDv7 generation utility
* Repository updates
* DTO updates
* New API usage of UUID
* Tests

Maintain full backward compatibility with the legacy system.
