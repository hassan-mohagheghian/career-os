# TDD Strategy

## Approach

The refactoring follows a **test-after** strategy for structural migration:

1. Verify existing tests pass (148 tests in `app/server/tests/`)
2. Move code into new structure
3. Verify tests still pass
4. Add new tests for new code (entities, value objects, use cases)

## Test Levels

### Unit Tests (Domain)
- Test entity creation and methods
- Test value object equality and behavior
- Test use case logic with mock repositories

### Integration Tests (Infrastructure)
- Test SQLAlchemy repository implementations
- Test database queries against in-memory SQLite

### API Tests (Presentation)
- Test FastAPI endpoints with TestClient
- Test request/response schemas

## Running Tests

```bash
# Core tests (queue, services)
python -m pytest app/server/tests/test_core/ app/server/tests/test_services/ -q

# API tests (requires httpx2)
python -m pytest app/server/tests/test_api/ -q

# All tests
python -m pytest app/server/tests/ -q
```

## Test Fixtures

- `conftest.py` provides in-memory SQLite session
- `TestClient` for API endpoint testing
- `sa_session` for repository testing
