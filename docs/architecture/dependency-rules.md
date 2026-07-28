# Dependency Rules

## Layer Dependencies

The architecture enforces strict dependency direction:

```
presentation → application → domain
```

### Presentation Layer
**Can depend on**:
- Application layer (use cases, services)
- Shared infrastructure (for cross-cutting concerns)

**Must NOT depend on**:
- Database directly
- Repository implementations
- External APIs
- Other bounded contexts' infrastructure

### Application Layer
**Can depend on**:
- Domain layer (entities, value objects, repository interfaces)
- Shared application (DTOs, exceptions)

**Must NOT depend on**:
- Presentation layer
- Database models
- Framework-specific code (FastAPI, SQLAlchemy)

### Domain Layer
**Can depend on**:
- Nothing outside itself
- Shared domain primitives (base entity, value object)

**Must NOT depend on**:
- FastAPI
- SQLAlchemy
- Pydantic
- CLI frameworks
- Any infrastructure code

### Infrastructure Layer
**Can depend on**:
- Domain layer (for repository interfaces it implements)
- Shared infrastructure (database, process management)
- External libraries (SQLAlchemy, HTTP clients)

**Must NOT depend on**:
- Presentation layer
- Application layer's use cases

## Import Rules

### Allowed Imports

```python
# ✅ Presentation → Application
from jobs.application.use_cases.list_jobs import ListJobsUseCase

# ✅ Presentation → Shared Infrastructure
from shared.infrastructure.database.session import get_session

# ✅ Application → Domain
from jobs.domain.entities.job import Job
from jobs.domain.repositories.job_repository import JobRepositoryInterface

# ✅ Infrastructure → Domain (implementing interfaces)
from jobs.domain.repositories.job_repository import JobRepositoryInterface

# ✅ Any context → Shared
from shared.application.exceptions import NotFoundError
from shared.domain.entity import BaseEntity
```

### Forbidden Imports

```python
# ❌ Domain → Infrastructure
from jobs.infrastructure.models.job_model import JobModel  # WRONG in domain

# ❌ Domain → Presentation
from jobs.presentation.api.schemas.jobs import JobSchema  # WRONG in domain

# ❌ Application → Infrastructure
from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository  # WRONG in application

# ❌ Cross-domain infrastructure
from companies.infrastructure.repositories.sa_company_repository import SQLAlchemyCompanyRepository  # WRONG in jobs context
```

## Shared Kernel Rules

The shared kernel (`shared/`) may be imported by any bounded context, but:

1. **No domain-specific logic** in shared
2. **No cross-domain leakage** — shared provides primitives, not business logic
3. **Infrastructure is shared** — database, queue, websocket, process management

## Circular Dependency Prevention

- Use lazy imports (`__getattr__`) in `__init__.py` files
- Import repository interfaces (not implementations) in application layer
- Use dependency injection for cross-context communication
- Keep shared kernel free of bounded context imports
