# Dependency Injection Strategy

## Overview

FastAPI's built-in `Depends()` system provides a clean, testable dependency injection mechanism. This replaces Flask's global mutable state pattern with explicit, type-safe dependencies.

## Core Principles

1. **Explicit over implicit** — all dependencies declared in function signatures
2. **Interface-based** — depend on abstractions, not implementations
3. **Scoped** — dependencies have clear lifetimes (request, application, singleton)
4. **Testable** — easy to mock/replace in tests

## Dependency Categories

### 1. Database Connection

```python
# infrastructure/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager

def get_db():
    """Yield a database session for the request lifetime."""
    engine = create_engine(f"sqlite:///{settings.db_path}")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 2. Repository Dependencies

```python
# dependencies.py
from apps.backend.infrastructure.database.job_repository import JobRepository
from apps.backend.infrastructure.database.company_repository import CompanyRepository
from apps.backend.infrastructure.database.skill_repository import SkillRepository

async def get_job_repository(db=Depends(get_db)) -> JobRepository:
    return JobRepository(db)

async def get_company_repository(db=Depends(get_db)) -> CompanyRepository:
    return CompanyRepository(db)

async def get_skill_repository(db=Depends(get_db)) -> SkillRepository:
    return SkillRepository(db)
```

### 3. Service Dependencies

```python
from apps.backend.application.services.job_service import JobService
from apps.backend.application.services.company_service import CompanyService
from apps.backend.application.services.insight_service import InsightService

async def get_job_service(repo=Depends(get_job_repository)) -> JobService:
    return JobService(repo)

async def get_company_service(repo=Depends(get_company_repository)) -> CompanyService:
    return CompanyService(repo)

async def get_insight_service(repo=Depends(get_job_repository)) -> InsightService:
    return InsightService(repo)
```

### 4. AI Dependencies

```python
from app.ai.service import get_llm_service

async def get_llm():
    """Get LLM service instance."""
    return get_llm_service()
```

### 5. Configuration Dependencies

```python
from apps.backend.config import settings

def get_settings() -> Settings:
    return settings
```

### 6. WebSocket Dependencies

```python
from apps.backend.infrastructure.websocket.manager import ConnectionManager

_manager: ConnectionManager | None = None

def get_connection_manager() -> ConnectionManager:
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
```

## Dependency Graph

```
Router
  ├── Depends(get_job_service)
  │     └── Depends(get_job_repository)
  │           └── Depends(get_db)
  ├── Depends(get_company_service)
  │     └── Depends(get_company_repository)
  │           └── Depends(get_db)
  ├── Depends(get_llm)
  └── Depends(get_connection_manager)
```

## Request Lifecycle

```python
# FastAPI automatically manages dependency lifetimes:
# 1. Router receives request
# 2. Resolves Depends() chain
# 3. Creates connections/repositories/services
# 4. Calls route handler
# 5. Cleans up (closes connections, etc.)

@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    service: JobService = Depends(get_job_service),  # Resolved here
):
    return await service.get_by_id(job_id)
    # Dependencies cleaned up after response
```

## Singleton vs Transient vs Scoped

| Dependency | Lifetime | Pattern |
|------------|----------|---------|
| Database connection | Scoped (per request) | `Depends(get_db)` |
| Repository | Scoped (per request) | Created per request |
| Service | Scoped (per request) | Created per request |
| LLM Service | Singleton | Module-level cache |
| Connection Manager | Singleton | Module-level instance |
| Settings | Singleton | Module-level instance |

### Singleton Pattern

```python
# For truly global, stateless services
_llm_service = None

def get_llm_service():
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
```

## Testing with Dependency Override

### Override in Tests

```python
# tests/conftest.py
from fastapi.testclient import TestClient
from apps.backend.main import app
from apps.backend.dependencies import get_job_repository
from tests.mocks import MockJobRepository

def override_job_repository():
    return MockJobRepository()

app.dependency_overrides[get_job_repository] = override_job_repository

client = TestClient(app)

def test_list_jobs():
    response = client.get("/api/jobs")
    assert response.status_code == 200
```

### Mock Repository

```python
# tests/mocks/mock_job_repository.py
from apps.backend.domain.repositories.job_repository import IJobRepository

class MockJobRepository(IJobRepository):
    def __init__(self):
        self.jobs = []
    
    async def get_by_id(self, job_id: str):
        return next((j for j in self.jobs if j.id == job_id), None)
    
    async def list_all(self):
        return self.jobs
    
    async def create(self, job):
        self.jobs.append(job)
        return job
```

## Avoiding Anti-Patterns

### Global Mutable State

```python
# BAD: Global mutable state
current_user = None

@router.get("/jobs")
async def list_jobs():
    return db.execute("SELECT * FROM jobs WHERE user_id=?", (current_user.id,))

# GOOD: Dependency injection
@router.get("/jobs")
async def list_jobs(
    user: User = Depends(get_current_user),
    service: JobService = Depends(get_job_service),
):
    return await service.list_by_user(user.id)
```

### Hidden Dependencies

```python
# BAD: Hidden dependency via module import
from apps.backend.database import get_db  # Implicit dependency

@router.get("/jobs")
async def list_jobs():
    conn = get_db()  # Where did this come from?
    return conn.query(Job).all()

# GOOD: Explicit dependency
@router.get("/jobs")
async def list_jobs(db=Depends(get_db)):
    return db.query(Job).all()
```

### Tight Coupling

```python
# BAD: Direct service instantiation
@router.get("/jobs")
async def list_jobs():
    repo = JobRepository(db)  # Tightly coupled
    service = JobService(repo)  # Tightly coupled
    return await service.list_jobs()

# GOOD: Dependency injection
@router.get("/jobs")
async def list_jobs(service: JobService = Depends(get_job_service)):
    return await service.list_jobs()
```

## Complex Dependencies

### Factory Pattern

```python
def get_job_service_factory():
    """Factory for creating job services with custom config."""
    def factory(config: ServiceConfig = Depends(get_service_config)):
        repo = JobRepository(db, config.batch_size)
        return JobService(repo, config.retry_count)
    return factory
```

### Conditional Dependencies

```python
async def get_ai_provider(provider_name: str = Depends(get_provider_name)):
    if provider_name == "mimo":
        return MimoProvider()
    elif provider_name == "openai":
        return OpenAIProvider()
    else:
        return LocalProvider()
```

### Chained Dependencies

```python
# Dependencies can depend on other dependencies
async def get_db_pool(db_path: str = Depends(get_db_path)):
    return create_pool(db_path)

async def get_db(pool=Depends(get_db_pool)):
    async with pool.acquire() as conn:
        yield conn

async def get_job_repo(db=Depends(get_db)):
    return JobRepository(db)
```

## Migration from Flask

### Before (Flask)

```python
# Global state
db = get_db()
socketio = SocketIO(app)

@jobs_bp.route('/api/jobs')
def list_jobs():
    conn = get_db()  # Global function
    jobs = conn.query(Job).all()
    return jsonify(jobs)
```

### After (FastAPI)

```python
# Explicit dependencies
@router.get("/jobs")
async def list_jobs(
    service: JobService = Depends(get_job_service),
):
    return await service.list_jobs()
```

### Key Changes

| Flask Pattern | FastAPI Pattern |
|---------------|-----------------|
| `get_db()` global | `Depends(get_db)` |
| `request.json` | Pydantic model parameter |
| `jsonify()` | Return dict (auto-serialized) |
| `@bp.route()` | `@router.get()` |
| Global `socketio` | `Depends(get_connection_manager)` |
| `threading.Thread()` | `asyncio.create_task()` |
