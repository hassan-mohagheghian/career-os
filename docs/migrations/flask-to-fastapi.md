# Flask to FastAPI Migration

## Migration Principles

1. **Preserve behavior** — every endpoint must return identical responses
2. **Incremental migration** — run Flask and FastAPI side-by-side during transition
3. **No big bang** — feature-by-feature migration with rollback capability
4. **Test at every step** — each phase validated before proceeding

## Phase 1: Preparation

**Duration:** 1-2 days
**Risk:** Low
**Goal:** Prepare codebase for migration without changing behavior

### Tasks

1. **Create FastAPI entry point**
   - Create `app/server/main.py` with FastAPI app
   - Configure lifespan, CORS, middleware
   - Mount under `/api/v1` prefix

2. **Set up dependency injection**
   - Create `app/server/dependencies.py`
   - Move `get_db()` to FastAPI `Depends()` pattern
   - Create repository/service dependencies

3. **Create Pydantic models**
   - Create `app/server/schemas/` directory
   - Define request/response models for each feature
   - Validate models match existing JSON responses

4. **Create test infrastructure**
   - Set up `httpx.AsyncClient` for async testing
   - Create test fixtures for database, services
   - Write tests for existing Flask endpoints

### Validation Criteria

- [ ] FastAPI app starts without errors
- [ ] Pydantic models validate existing response formats
- [ ] Test infrastructure works
- [ ] Existing Flask app unchanged

### Rollback

- Delete new files, no changes to existing code

---

## Phase 2: FastAPI Foundation

**Duration:** 2-3 days
**Risk:** Medium
**Goal:** Create FastAPI skeleton with core infrastructure

### Tasks

1. **Core infrastructure**
   - Implement `ConnectionManager` for WebSocket
   - Implement `Broadcaster` adapter for WebSocket events
   - Set up structlog for FastAPI
   - Configure error handling middleware

2. **Database layer**
   - Create `app/server/infrastructure/database/`
   - Implement repository interfaces
   - Create repository implementations (copy from existing)
   - Unify `get_db()` into single implementation

3. **WebSocket support**
   - Create `app/server/api/v1/websocket.py`
   - Implement WebSocket endpoint
   - Port SocketIO event handlers
   - Test real-time communication

4. **Background tasks**
   - Refactor `JobQueueManager` for async
   - Create `app/server/infrastructure/workers/`
   - Implement worker classes
   - Test background processing

### Validation Criteria

- [ ] FastAPI serves health check endpoint
- [ ] WebSocket connections work
- [ ] Background tasks execute correctly
- [ ] All existing tests still pass

### Rollback

- Keep FastAPI code, continue using Flask

---

## Phase 3: Feature Migration

**Duration:** 5-7 days
**Risk:** Medium
**Goal:** Migrate features one-by-one from Flask to FastAPI

### Migration Order

1. **System endpoints** (low risk)
   - Dashboard, generation history, cities
   - Scoring rules
   - API docs

2. **Skills** (medium complexity)
   - CRUD operations
   - Merge, hide/restore
   - Categories, stats

3. **Companies** (medium complexity)
   - CRUD operations
   - Notes, links
   - Intelligence endpoints

4. **Jobs** (medium complexity)
   - CRUD operations
   - Scoring, reprocessing
   - Summaries

5. **Pending** (high complexity)
   - Queue management
   - SSE streaming
   - Real-time progress

6. **Insights** (high complexity)
   - Generation endpoints
   - Progress streaming
   - Skills intelligence

7. **Resumes** (high complexity)
   - Generation endpoints
   - Cover letter generation
   - Real-time progress

8. **Skill Roadmaps** (high complexity)
   - CRUD operations
   - AI generation
   - Progress tracking

### Per-Feature Migration Steps

For each feature:

1. **Create router** in `api/v1/<feature>.py`
2. **Create service** in `application/services/<feature>_service.py`
3. **Create repository** in `infrastructure/database/<feature>_repository.py`
4. **Create Pydantic models** in `schemas/<feature>.py`
5. **Write tests** for FastAPI endpoints
6. **Compare responses** with Flask endpoints
7. **Switch traffic** to FastAPI
8. **Monitor for issues**

### Validation Criteria

- [ ] All endpoints migrated
- [ ] Response formats identical
- [ ] All tests pass
- [ ] Real-time features work
- [ ] Background tasks work

### Rollback

- Switch traffic back to Flask
- FastAPI code remains for retry

---

## Phase 4: Flask Removal

**Duration:** 1-2 days
**Risk:** Low
**Goal:** Remove Flask code and clean up

### Tasks

1. **Remove Flask dependencies**
   - Remove `flask`, `flask-socketio` from requirements
   - Remove Flask-specific middleware
   - Remove Flask blueprints

2. **Clean up imports**
   - Remove `ai_compat.py` shim
   - Update import paths
   - Remove dead code

3. **Update documentation**
   - Update architecture docs
   - Update API docs
   - Update deployment docs

4. **Final validation**
   - Run full test suite
   - Manual testing of all features
   - Performance benchmarking

### Validation Criteria

- [ ] No Flask imports remain
- [ ] All tests pass
- [ ] Application starts cleanly
- [ ] All features work
- [ ] Performance acceptable

### Rollback

- Restore Flask code from git
- Reinstall Flask dependencies

---

## Rollback Strategy

### Feature-Level Rollback

```python
# In main.py, route traffic based on feature flag
if settings.use_fastapi_features:
    app.include_router(api_router)
else:
    app.include_router(flask_blueprint)
```

### Full Rollback

```bash
# Revert to Flask
git checkout HEAD~1
pip install -r requirements-flask.txt
./start
```

## Testing Strategy

### Response Comparison Tests

```python
# tests/migration/test_response_comparison.py
import httpx
import pytest

@pytest.mark.asyncio
async def test_jobs_response_matches(flask_client, fastapi_client):
    """Verify FastAPI returns same response as Flask."""
    flask_response = await flask_client.get("/api/jobs")
    fastapi_response = await fastapi_client.get("/api/v1/jobs")
    
    assert flask_response.status_code == fastapi_response.status_code
    assert flask_response.json() == fastapi_response.json()
```

### Migration Test Matrix

| Feature | Flask Endpoint | FastAPI Endpoint | Response Match | Real-time | Background |
|---------|---------------|------------------|----------------|-----------|------------|
| Jobs | `/api/jobs` | `/api/v1/jobs` | ✅ | — | ✅ |
| Companies | `/api/companies` | `/api/v1/companies` | ✅ | — | ✅ |
| Skills | `/api/skills` | `/api/v1/skills` | ✅ | — | — |
| Pending | `/api/pending` | `/api/v1/pending` | ✅ | SSE | ✅ |
| Insights | `/api/insights` | `/api/v1/insights` | ✅ | SSE | ✅ |
| Resumes | `/api/resumes` | `/api/v1/resumes` | ✅ | SSE | ✅ |
| Roadmaps | `/api/skill-roadmaps` | `/api/v1/skill-roadmaps` | ✅ | SSE | ✅ |

## Risk Mitigation

### Risk: Response Format Differences

**Mitigation:**
- Create Pydantic models that match existing JSON exactly
- Write comparison tests
- Manual review of edge cases

### Risk: WebSocket Compatibility

**Mitigation:**
- Port Broadcaster class to use WebSocket
- Test real-time features extensively
- Keep SocketIO fallback option

### Risk: Background Task Failures

**Mitigation:**
- Port JobQueueManager carefully
- Test with production-like load
- Monitor error rates

### Risk: Performance Regression

**Mitigation:**
- Benchmark before/after
- Profile hot paths
- Optimize database queries

## Success Criteria

- [ ] All endpoints migrated and working
- [ ] All tests pass
- [ ] Real-time features work
- [ ] Background tasks work
- [ ] No performance regression
- [ ] Documentation updated
- [ ] Flask code removed
- [ ] Deployment updated
