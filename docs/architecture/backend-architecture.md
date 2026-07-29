# Backend Architecture

## Executive Summary

This document defines the target FastAPI backend architecture for the Job Search Intelligence platform. The migration from Flask to FastAPI preserves all existing functionality while establishing a production-grade foundation based on Clean Architecture, DDD, and SOLID principles.

**Key outcomes:**
- Native async/await for concurrent I/O operations
- Type-safe request/response validation via Pydantic v2
- Scalable dependency injection replacing global mutable state
- Unified WebSocket support replacing dual SocketIO systems
- Foundation for future PostgreSQL migration and ORM adoption

## Target Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| HTTP | FastAPI + Uvicorn | ASGI server with async support |
| Validation | Pydantic v2 | Request/response schemas, settings |
| Database | SQLite → PostgreSQL (future) | Raw SQL preserved, async via aiosqlite |
| Logging | structlog | Structured JSON logging |
| Testing | pytest + httpx | Async API testing |
| Config | pydantic-settings | Environment-based configuration |
| WebSockets | FastAPI native | Real-time event streaming |

## Architectural Layers

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                     │
│              (FastAPI Routers + WebSocket)                │
│         request validation, response serialization       │
├─────────────────────────────────────────────────────────┤
│                   Application Layer                      │
│            (Services + Use Cases + DTOs)                  │
│         orchestration, business workflow                  │
├─────────────────────────────────────────────────────────┤
│                     Domain Layer                         │
│          (Entities + Value Objects + Events)              │
│         business rules, invariants                        │
├─────────────────────────────────────────────────────────┤
│                 Infrastructure Layer                     │
│        (DB + External APIs + File System)                 │
│         persistence, third-party integration              │
├─────────────────────────────────────────────────────────┤
│                    Shared/Core Layer                      │
│          (Config + Logging + Dependencies)                │
│         cross-cutting concerns                            │
└─────────────────────────────────────────────────────────┘
```

### Presentation Layer

**Responsibility:** Handle HTTP requests, validate input, serialize output.

- FastAPI Routers organized by feature
- Pydantic models for request/response validation
- WebSocket endpoint handlers
- Error handling middleware
- CORS configuration

**Rules:**
- Routers contain zero business logic
- All input validated via Pydantic models
- All output serialized via Pydantic models
- Dependencies injected via `Depends()`

### Application Layer

**Responsibility:** Orchestrate business workflows, coordinate domain objects.

- Service classes (one per feature)
- Use case functions for complex operations
- DTOs for data transfer between layers
- Event dispatching for async operations

**Rules:**
- Services depend on domain interfaces, not implementations
- Services are stateless (no mutable class attributes)
- Background tasks dispatched via FastAPI's `BackgroundTasks` or task queue

### Domain Layer

**Responsibility:** Define business rules, entities, and invariants.

- Domain entities (Job, Company, Skill, etc.)
- Value objects (Score, Status, etc.)
- Domain events (ProcessingComplete, StatusUpdate)
- Repository interfaces (abstract base classes)
- Domain services (pure business logic)

**Rules:**
- Domain layer has zero external dependencies
- No framework imports (no FastAPI, no SQLAlchemy)
- Business rules enforced via entity methods
- Invariants validated at construction time

### Infrastructure Layer

**Responsibility:** Implement external integrations and persistence.

- Database repository implementations
- LLM provider adapters
- HTTP clients for external APIs
- WebSocket broadcaster
- LangGraph workflow graphs (AI Agent Layer)

**Rules:**
- Implements domain interfaces
- Framework-specific code isolated here
- No business logic in infrastructure
- **No file I/O in job processing** — all pipeline state flows through LangGraph state
- Job processing state managed entirely in memory via LangGraph `BaseState`/`JobProcessingState`

### Shared/Core Layer

**Responsibility:** Cross-cutting concerns used across all layers.

- Configuration management
- Logging setup
- Dependency injection container
- Common utilities
- Error types

## Request Flow

```
HTTP Request
    │
    ▼
┌─────────────┐
│  Middleware  │  CORS, logging, error handling
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Router    │  Route matching, dependency resolution
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Depends()  │  DB connection, auth, config injection
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Service   │  Business workflow orchestration
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Repository │  Database queries (SQLAlchemy ORM)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database   │  SQLite / PostgreSQL
└─────────────┘
```

## Error Handling Strategy

### Error Hierarchy

```python
class AppError(Exception):
    """Base application error."""
    status_code: int = 500
    detail: str = "Internal server error"

class NotFoundError(AppError):
    status_code: int = 404

class ValidationError(AppError):
    status_code: int = 422

class ConflictError(AppError):
    status_code: int = 409

class ExternalServiceError(AppError):
    status_code: int = 502
```

### Error Response Format

```json
{
    "error": {
        "code": "NOT_FOUND",
        "message": "Job not found",
        "details": {"job_num": 123}
    }
}
```

### Exception Handlers

```python
@app.exception_handler(AppError)
async def app_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.detail}}
    )
```

## Background Processing

### Strategy: FastAPI BackgroundTasks + asyncio

- **Short tasks** (< 30s): FastAPI `BackgroundTasks`
- **Long tasks** (AI generation): `asyncio.create_task()` with progress streaming via WebSocket
- **Queue management**: Existing `JobQueueManager` refactored to use asyncio primitives

## Job Processing Pipeline (LangGraph)

### State Management (No File I/O)

All job processing state flows through LangGraph state — no temp files are written to disk.

**State flow:**
```
URL/Notes/Links → load_context → validate → fetch → extract_raw → clean →
extract_struct → analyze → skills → score → summary → persist → completion
```

**Key design decisions:**
- `BaseState` TypedDict carries all data in `metadata`, `context`, and `errors` fields
- Resume and LinkedIn data loaded from DB into `context` at pipeline start (no temp files)
- LLM calls go through `LLMService` abstraction (file-free)
- Results persisted directly to database via repositories
- `persist_results` node saves job + summary in a single DB transaction

**Cancellation support:**
- `WorkerBase` checks pending item status between steps
- LangGraph graph runs atomically — cancellation is checked before/after pipeline execution

### Graph Architecture

```
ai/infrastructure/graphs/
├── runtime/
│   ├── graph.py        # GraphBuilder + CompiledGraph (wraps LangGraph StateGraph)
│   └── state.py        # BaseState, JobProcessingState, output models
├── job/
│   └── graph.py        # 13-node job processing graph
├── company/
├── resume/
├── skills/
└── insights/
```

The `GraphBuilder` supports both LangGraph (`StateGraph`) and sequential fallback backends.
Job processing uses the `JobWorker` class which compiles and invokes the job graph.

### Concurrency Model

```python
# Background task dispatch
@router.post("/jobs/{num}/process")
async def process_job(num: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_job_task, num)
    return {"status": "queued"}

# Long-running with progress
@router.post("/insights/refresh")
async def refresh_insights():
    task = asyncio.create_task(generate_insights_with_progress())
    return {"task_id": task.get_name()}
```

## WebSocket Architecture

### Connection Management

```python
class ConnectionManager:
    """Manages WebSocket connections by room."""
    
    def __init__(self):
        self.active: dict[str, set[WebSocket]] = {}
    
    async def connect(self, ws: WebSocket, room: str):
        await ws.accept()
        self.active.setdefault(room, set()).add(ws)
    
    def disconnect(self, ws: WebSocket, room: str):
        self.active.get(room, set()).discard(ws)
    
    async def broadcast(self, room: str, data: dict):
        for ws in self.active.get(room, set()):
            await ws.send_json(data)
```

### Event Mapping (SocketIO → WebSocket)

| SocketIO Event | WebSocket Room | Direction |
|----------------|----------------|-----------|
| `watch_pending` | `pending_{id}` | Client → Server |
| `pending:update` | `pending_{id}` | Server → Client |
| `pending:log` | `pending_{id}` | Server → Client |
| `pending:complete` | `pending_{id}` | Server → Client |
| `watch_company` | `company_{id}` | Client → Server |
| `company:update` | `company_{id}` | Server → Client |
| `watch_generation` | `generation_{id}` | Client → Server |
| `generation:update` | `generation_{id}` | Server → Client |

### Broadcaster Refactoring

The existing `Broadcaster` class already abstracts event emission. Only the transport layer changes:

```python
# Before (SocketIO)
socketio.emit('pending:update', data, room=f'pending_{id}')

# After (WebSocket)
await connection_manager.broadcast(f'pending_{id}', {"event": "pending:update", "data": data})
```

## Logging Architecture

### structlog Configuration

```python
import structlog

def setup_logging(log_dir: str, level: str):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty()
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

### Log Categories

| Category | Purpose | Example |
|----------|---------|---------|
| `request` | HTTP request logging | `GET /api/jobs 200 45ms` |
| `pipeline` | Job processing steps | `job.fetch url=... status=200` |
| `ai` | LLM call tracking | `llm.generate provider=mimo tokens=1500` |
| `websocket` | Connection events | `ws.connect room=pending_123` |
| `error` | Error tracking | `error.processing job=123 step=extract` |

### Request Logging Middleware

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    log = get_logger("request")
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    log.info("request", method=request.method, path=request.url.path, 
             status=response.status_code, duration_ms=round(duration * 1000))
    return response
```

## Configuration Management

### Settings Class (pydantic-settings)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    db_path: str = "db/jobs.db"
    
    # AI
    ai_provider: str = "mimo"
    ai_openai_api_key: str | None = None
    
    # Processing
    queue_concurrency: int = 2
    
    # Server
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]
    
    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Environment Profiles

| Variable | Development | Production | Testing |
|----------|-------------|------------|---------|
| `DB_PATH` | `db/jobs.db` | `/data/jobs.db` | `:memory:` |
| `DEBUG` | `true` | `false` | `false` |
| `LOG_LEVEL` | `DEBUG` | `INFO` | `WARNING` |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | `["https://app.example.com"]` | `["*"]` |
| `QUEUE_CONCURRENCY` | `2` | `4` | `1` |

## Security Considerations

### Input Validation
- All request bodies validated via Pydantic models
- Query parameters validated via FastAPI's `Query()`
- Path parameters typed and validated automatically

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### SQL Injection Prevention
- Parameterized queries preserved (existing pattern)
- No string interpolation in SQL (existing pattern enforced)
- Future: SQLAlchemy Core parameterization

## Performance Considerations

### Async Database Access
- `aiosqlite` for async SQLite operations
- Connection pooling via `asyncpg` (future PostgreSQL)
- Read replicas for read-heavy endpoints (future)

### Caching Strategy
- In-memory cache for frequently accessed data (skills, rules)
- ETag/If-None-Match for static data endpoints
- Cache invalidation on data mutation

### Connection Limits
- Uvicorn workers: 1 (SQLite single-writer)
- WebSocket connections: unbounded (in-memory)
- Database connections: 1 per request (no pooling for SQLite)
