# Backend Testing Strategy

## Overview

This document defines the testing approach for the FastAPI backend, covering unit tests, integration tests, API tests, and migration tests.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Unit tests
│   ├── domain/                   # Domain entity tests
│   │   ├── test_job.py
│   │   ├── test_company.py
│   │   └── test_skill.py
│   ├── application/              # Service tests
│   │   ├── test_job_service.py
│   │   ├── test_company_service.py
│   │   └── test_insight_service.py
│   └── infrastructure/           # Infrastructure tests
│       ├── test_job_repository.py
│       └── test_broadcaster.py
├── integration/                   # Integration tests
│   ├── api/                      # API endpoint tests
│   │   ├── test_jobs.py
│   │   ├── test_companies.py
│   │   ├── test_skills.py
│   │   ├── test_pending.py
│   │   ├── test_insights.py
│   │   ├── test_resumes.py
│   │   └── test_skill_roadmaps.py
│   ├── database/                 # Database operation tests
│   │   ├── test_migrations.py
│   │   └── test_repositories.py
│   └── websocket/                # WebSocket tests
│       ├── test_connection.py
│       └── test_events.py
└── migration/                     # Migration validation tests
    ├── test_response_comparison.py
    └── test_feature_parity.py
```

## Test Categories

### 1. Unit Tests

**Purpose:** Test individual components in isolation.
**Speed:** Fast (< 100ms per test)
**Dependencies:** None (mocked)

#### Domain Entity Tests

```python
# tests/unit/domain/test_job.py
from app.server.domain.entities.job import Job
from app.server.domain.value_objects.score import Score

def test_job_creation():
    job = Job(
        num=1,
        url="https://example.com/job",
        title="Software Engineer",
        company="Tech Corp",
    )
    assert job.num == 1
    assert job.url == "https://example.com/job"

def test_job_score_calculation():
    job = Job(
        num=1,
        url="https://example.com/job",
        fit_score=8.0,
        success_score=7.0,
    )
    assert job.overall_score == 7.5

def test_job_validation():
    with pytest.raises(ValidationError):
        Job(num=1, url="", title="Test")  # Empty URL
```

#### Service Tests

```python
# tests/unit/application/test_job_service.py
import pytest
from app.server.application.services.job_service import JobService
from tests.mocks import MockJobRepository

@pytest.fixture
def service():
    repo = MockJobRepository()
    return JobService(repo)

@pytest.mark.asyncio
async def test_list_jobs(service):
    jobs = await service.list_jobs()
    assert isinstance(jobs, list)

@pytest.mark.asyncio
async def test_get_job_not_found(service):
    with pytest.raises(NotFoundError):
        await service.get_by_num(999)
```

#### Repository Tests

```python
# tests/unit/infrastructure/test_job_repository.py
import pytest
from app.server.infrastructure.database.job_repository import JobRepository

@pytest.mark.asyncio
async def test_create_job(test_db):
    repo = JobRepository(test_db)
    job = await repo.create({
        "url": "https://example.com/job",
        "title": "Software Engineer",
    })
    assert job.num is not None

@pytest.mark.asyncio
async def test_get_job_by_num(test_db):
    repo = JobRepository(test_db)
    # Create job first
    job = await repo.create({"url": "https://example.com/job"})
    # Retrieve it
    retrieved = await repo.get_by_num(job.num)
    assert retrieved.url == job.url
```

### 2. Integration Tests

**Purpose:** Test component interactions.
**Speed:** Medium (< 1s per test)
**Dependencies:** Database (in-memory SQLite)

#### API Endpoint Tests

```python
# tests/integration/api/test_jobs.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_jobs(client: AsyncClient):
    response = await client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

@pytest.mark.asyncio
async def test_create_job(client: AsyncClient):
    response = await client.post(
        "/api/jobs",
        json={"url": "https://example.com/job"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://example.com/job"

@pytest.mark.asyncio
async def test_get_job(client: AsyncClient):
    # Create job first
    create_response = await client.post(
        "/api/jobs",
        json={"url": "https://example.com/job"},
    )
    job_num = create_response.json()["num"]
    
    # Get job
    response = await client.get(f"/api/jobs/{job_num}")
    assert response.status_code == 200
    assert response.json()["num"] == job_num

@pytest.mark.asyncio
async def test_update_job(client: AsyncClient):
    # Create job
    create_response = await client.post(
        "/api/jobs",
        json={"url": "https://example.com/job"},
    )
    job_num = create_response.json()["num"]
    
    # Update job
    response = await client.put(
        f"/api/jobs/{job_num}",
        json={"title": "Updated Title"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"

@pytest.mark.asyncio
async def test_delete_job(client: AsyncClient):
    # Create job
    create_response = await client.post(
        "/api/jobs",
        json={"url": "https://example.com/job"},
    )
    job_num = create_response.json()["num"]
    
    # Delete job
    response = await client.delete(f"/api/jobs/{job_num}")
    assert response.status_code == 200
    
    # Verify deleted
    get_response = await client.get(f"/api/jobs/{job_num}")
    assert get_response.status_code == 404
```

#### Database Integration Tests

```python
# tests/integration/database/test_repositories.py
import pytest
from app.server.infrastructure.database.connection import get_db

@pytest.mark.asyncio
async def test_database_connection(test_db):
    async with get_db() as conn:
        result = await conn.execute("SELECT 1")
        assert result.fetchone()[0] == 1

@pytest.mark.asyncio
async def test_migration_runs(test_db):
    from app.server.infrastructure.database.migrations import run_migrations
    await run_migrations(test_db)
    
    # Verify tables exist
    tables = await test_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    table_names = [row[0] for row in tables.fetchall()]
    assert "jobs" in table_names
    assert "companies" in table_names
```

### 3. WebSocket Tests

```python
# tests/integration/websocket/test_connection.py
import pytest
from fastapi.testclient import TestClient

def test_websocket_connection(client: TestClient):
    with client.websocket_connect("/ws") as ws:
        # Send watch event
        ws.send_json({"type": "watch", "room": "test_room"})
        
        # Connection should succeed
        assert ws.receive_text() is not None

def test_websocket_broadcast(client: TestClient, connection_manager):
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "watch", "room": "test_room"})
        
        # Broadcast to room
        await connection_manager.broadcast(
            "test_room",
            {"type": "test:event", "data": {"key": "value"}}
        )
        
        # Receive broadcast
        data = ws.receive_json()
        assert data["type"] == "test:event"
```

### 4. Migration Tests (Completed)

The Flask-to-FastAPI migration is complete. Response comparison tests that ran Flask and FastAPI side-by-side have been removed. Only the FastAPI test suite remains.

## Test Fixtures

### Shared Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient, ASGITransport
from app.server.main import app
from app.server.dependencies import get_db
from app.server.infrastructure.database.models import Base

@pytest.fixture
def test_db():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    
    yield session
    session.close()

@pytest.fixture
async def client(test_db):
    """Create async test client."""
    app.dependency_overrides[get_db] = lambda: test_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    from tests.mocks import MockLLMService
    return MockLLMService()
```

## Test Configuration

### pytest.ini

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    migration: Migration validation tests
    slow: Slow tests
```

### pyproject.toml

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["app/server"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.",
]
```

## Running Tests

### Full Test Suite

```bash
pytest
```

### By Category

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Migration tests only
pytest tests/migration/

# Fast tests (exclude slow)
pytest -m "not slow"
```

### With Coverage

```bash
pytest --cov=app/server --cov-report=html
```

### Specific Test

```bash
pytest tests/integration/api/test_jobs.py::test_list_jobs -v
```

## Test Data Management

### Test Data Factory

```python
# tests/factories.py
from faker import Faker

fake = Faker()

def create_test_job(**overrides):
    return {
        "url": fake.url(),
        "title": fake.job(),
        "company": fake.company(),
        "location": fake.city(),
        "description": fake.text(),
        **overrides,
    }

def create_test_company(**overrides):
    return {
        "name": fake.company(),
        "industry": fake.job(),
        "tech_stack": ["Python", "FastAPI"],
        **overrides,
    }
```

### Database Cleanup

```python
# tests/conftest.py
@pytest.fixture(autouse=True)
async def cleanup_db(test_db):
    """Clean up database after each test."""
    yield
    # Delete all data (keep schema)
    tables = ["jobs", "companies", "skills", "resumes", "insights"]
    for table in tables:
        await test_db.execute(f"DELETE FROM {table}")
    await test_db.commit()
```

## CI Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest --cov=app/server
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```
