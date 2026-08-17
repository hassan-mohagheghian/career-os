# API Design

## Overview

This document defines the FastAPI API conventions, request/response patterns, and error handling for the Job Search Intelligence platform.

## Router Organization

Routes are organized by DDD bounded context. Each context owns its `presentation/api/` layer.

```python
# shared/presentation/api/root_router.py
from fastapi import APIRouter

api_router = APIRouter(prefix="/api")

api_router.include_router(jobs_v2_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(companies_v2_router, prefix="/companies", tags=["companies"])
api_router.include_router(skills_router, prefix="/skills", tags=["skills"])
api_router.include_router(insights_router, prefix="/insights", tags=["insights"])
api_router.include_router(process_router, prefix="/jobs", tags=["processing"])
api_router.include_router(executions_router, prefix="/processing", tags=["processing"])
api_router.include_router(rules_router, prefix="/rules", tags=["rules"])
api_router.include_router(dashboard_router, prefix="", tags=["dashboard"])
```

## Request Validation

### Pydantic Models

```python
# jobs/presentation/api/schemas/jobs.py
from pydantic import BaseModel, Field

class JobCreate(BaseModel):
    url: str = Field(..., description="Job posting URL")
    notes: str | None = Field(None, description="Additional notes")
    links: list[str] = Field(default_factory=list, description="Related links")

class JobUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    notes: str | None = None
    fit_score: float | None = Field(None, ge=0, le=10)
    success_score: float | None = Field(None, ge=0, le=10)
    overall_score: float | None = Field(None, ge=0, le=10)

class JobFilter(BaseModel):
    company: str | None = None
    location: str | None = None
    min_score: float | None = None
    max_score: float | None = None
    status: str | None = None
```

### Query Parameters

```python
from fastapi import Query

@router.get("/jobs")
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    company: str | None = Query(None, description="Filter by company"),
    min_score: float | None = Query(None, ge=0, le=10),
):
    ...
```

### Path Parameters

```python
from fastapi import Path

@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str = Path(..., description="Job UUID id"),
):
    ...
```

## Response Schemas

### Standard Response Format

```python
from pydantic import BaseModel

class ApiResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str | None = None

class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    per_page: int
    pages: int
```

### Job Response

```python
class JobResponse(BaseModel):
    id: str
    url: str
    title: str
    company: str
    location: str
    description: str
    notes: str
    fit_score: float
    success_score: float
    overall_score: float
    status: str
    created_at: str
    updated_at: str

class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    per_page: int
```

### Company Response

```python
class CompanyResponse(BaseModel):
    id: int
    name: str
    industry: str
    tech_stack: list[str]
    funding_stage: str
    visa_sponsorship: bool
    notes: str
    created_at: str

class CompanyIntelligenceResponse(BaseModel):
    company_id: int
    overview: str
    culture: str
    tech_stack: list[str]
    visa_policy: str
    last_updated: str
```

### Skill Response

```python
class SkillResponse(BaseModel):
    id: int
    name: str
    category: str
    confidence: float
    market_relevance: float
    source: str
    hidden: bool
    aliases: list[str]
    relationships: list[SkillRelationship]

class SkillRelationship(BaseModel):
    skill_id: int
    related_skill_id: int
    relationship_type: str  # related, similar, parent, child, alternative
```

## Error Handling

### Error Response Format

```python
class ErrorResponse(BaseModel):
    error: ErrorDetail

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None

# Example (not found):
{
    "error": {
        "code": "NOT_FOUND",
        "message": "Job not found",
        "details": {"job_id": "8f5b1c2e-…"}
    }
}

# Example (duplicate job):
{
    "error": {
        "code": "JOB_ALREADY_EXISTS",
        "message": "A Job with the same primary URL already exists.",
        "details": {
            "job_id": "8f5b1c2e-…",
            "job": {
                "id": "8f5b1c2e-…",
                "title": "Senior Backend Engineer",
                "company": "Acme GmbH",
                "company_id": "…",
                "company_type": "product",
                "location": "Berlin",
                "visa": "Yes",
                "salary": "€90k",
                "employment_types": ["Full-time"],
                "work_types": ["Remote"],
                "overall_score": 85,
                "fit_score": 80,
                "success_score": 90,
                "rank": 3,
                "tracking_status": "ready_to_apply",
                "url": "https://…",
                "updated_at": "…"
            }
        }
    }
}
```

The `job` summary mirrors the top-of-detail header so the UI can render the
existing job (scores, rank, identity rows) below the duplicate error and link to
its full details. `job_id` remains available for direct navigation.

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `PROCESSING_ERROR` | 500 | Background processing failed |
| `EXTERNAL_SERVICE_ERROR` | 502 | External API call failed |
| `RATE_LIMITED` | 429 | Too many requests |

### Exception Handlers

```python
# exceptions.py
class AppError(Exception):
    code: str = "INTERNAL_ERROR"
    status_code: int = 500
    detail: str = "Internal server error"

class NotFoundError(AppError):
    code: str = "NOT_FOUND"
    status_code: int = 404
    detail: str = "Resource not found"

class ValidationError(AppError):
    code: str = "VALIDATION_ERROR"
    status_code: int = 422
    detail: str = "Validation failed"

# middleware.py
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.detail,
                "details": getattr(exc, "details", None),
            }
        },
    )
```

## API Endpoints

### Jobs

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/jobs` | GET | — | `JobListResponse` | List jobs (paginated) |
| `/api/jobs/{id}` | GET | — | `JobResponse` | Get job by id |
| `/api/jobs` | POST | `JobCreate` | `JobResponse` | Create new job |
| `/api/jobs/{id}` | PATCH | `JobUpdate` | `JobDetailResponseSchema` | Update job |
| `/api/jobs/{id}` | DELETE | — | `204` | Delete job |
| `/api/jobs/{id}/process` | POST | — | `{"execution_id": "...", "status": "queued"}` | Process job |

### Companies

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/companies/list` | GET | — | `CompanyListResponse` | Paginated list (search/sort/filter, pinned, cursor) |
| `/api/companies/{id}` | GET | — | `CompanyDetailResponseSchema` | Get company + notes, links, intelligence, scores, jobs (single payload) |
| `/api/companies` | POST | `CompanyCreateRequest` | `CompanyCreateResponse` | Create company (`{name, notes, links, source, queue}` → `{id, name, status, execution_id?}`, 201) |
| `/api/companies/{id}` | PUT | `CompanyUpdateRequest` | `CompanyDetailResponseSchema` | Update company |
| `/api/companies/{id}` | DELETE | — | `204` | Hard-delete company (executions, links, intelligence) |
| `/api/companies/{id}/pinned` | PUT | `{pinned}` | `{id, pinned}` | Toggle company pinned |
| `/api/companies/{id}/main` | PUT | `{main_company_id}` | `CompanyDetailResponseSchema` | Set main company (relate aliases) |
| `/api/companies/{id}/reprocess` | POST | — | `{"status": "queued", "execution_id": "..."}` | Queue company for reprocessing |
| `/api/companies/{id}/notes` | GET | — | `CompanyNote[]` | List notes |
| `/api/companies/{id}/notes` | POST | `{content}` | `CompanyNote` | Add note (201) |
| `/api/companies/{id}/notes/{note_id}` | PUT | `{content}` | `CompanyNote` | Update note |
| `/api/companies/{id}/notes/{note_id}` | DELETE | — | `204` | Delete note |
| `/api/companies/{id}/links` | POST | `{url, title?, description?}` | `CompanyLink` | Add link (201) |
| `/api/companies/{id}/links/{link_id}` | PUT | `{url, title?, description?}` | `CompanyLink` | Update link |
| `/api/companies/{id}/links/{link_id}` | DELETE | — | `204` | Delete link |

> `{id}` values for companies are **UUID v7 strings** (migration
> `company_002_add_uuid_v7`); all company endpoints accept/take string ids.
>
> Company processing runs through the shared `ProcessingExecution` lifecycle
> (execution type `COMPANY_PROCESSING`), the same two-phase model as jobs: a
> context-preparation phase (no LLM) followed by a single-LLM-call analysis
> phase. List items include `latest_processing_execution`
> (`{id, status, started_at, finished_at}` or `null`). Live progress is streamed
> over `/api/sse/processing-events` with `target_type: "company"` and can be
> monitored via the Processing Drawer filtered to companies.

### Processing

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/processing/queue` | GET | — | `QueueSnapshotResponse` | Execution queue snapshot (jobs + companies) |
| `/api/processing/queue/{execution_id}` | DELETE | — | `{"success": true}` | Remove a queue entry |
| `/api/processing/executions/{execution_id}` | GET | — | `ExecutionDetailResponse` | Execution + workflow progress |
| `/api/processing/executions/{execution_id}/start` | POST | — | `{"status": "started"}` | Start a queued execution |
| `/api/processing/executions/{execution_id}/cancel` | POST | — | `{"status": "cancelled"}` | Cancel a running execution |
| `/api/processing/executions/{execution_id}/retry` | POST | — | `{"status": "queued"}` | Retry a failed execution |

### Skills

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/skills` | GET | — | `SkillListResponse` | List skills |
| `/api/skills/list` | GET | — | `SkillListResponse` | Paginated, searchable, filterable, sortable skill list (cursor-based) |
| `/api/skills` | POST | `SkillCreate` | `SkillResponse` | Create skill |
| `/api/skills/{id}` | PUT | `SkillUpdate` | `SkillResponse` | Update skill |
| `/api/skills/{id}` | GET | — | `SkillResponse` | Get single skill (aliases, tags) |
| `/api/skills/{id}` | DELETE | — | `{"success": true}` | Delete skill |
| `/api/skills/{id}/hide` | PATCH | — | `SkillResponse` | Soft-delete skill |
| `/api/skills/{id}/restore` | PATCH | — | `SkillResponse` | Restore hidden skill |
| `/api/skills/{id}/rename` | PATCH | `RenameSkill` | `SkillResponse` | Rename skill |
| `/api/skills/{id}/aliases` | POST | `SkillAliasAdd` | `SkillResponse` | Add an alias |
| `/api/skills/{id}/aliases` | DELETE | `?alias_name=` | `SkillResponse` | Remove an alias (query param so names with `/` work) |
| `/api/skills/{id}/jobs` | GET | — | `SkillJobsResponse` | Jobs that mention a skill (jobs-only mentions) |
| `/api/skills/merge` | POST | `MergeSkills` | `SkillResponse` | Merge skills (folds mentions) |
| `/api/skills/categories` | GET | — | `CategoryList` | List categories |
| `/api/skills/stats` | GET | — | `SkillStats` | Skill statistics |

### Insights

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/insights` | GET | — | `InsightsResponse` | Get all insights |
| `/api/insights/{section}` | GET | — | `SectionResponse` | Get section |
| `/api/insights/refresh` | POST | — | `{"status": "started"}` | Generate all sections |
| `/api/insights/{section}/refresh` | POST | — | `{"status": "started"}` | Generate section |
| `/api/insights/progress` | GET | — | `ProgressResponse` | Generation progress |
| `/api/insights/status` | GET | — | `StatusResponse` | Section statuses |
| `/api/insights/skills-intel` | GET | — | `SkillsIntelResponse` | Skills intelligence |
| `/api/insights/cancel` | POST | — | `{"success": true}` | Cancel generation |

### Dashboard

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/dashboard` | GET | — | `DashboardResponse` | Dashboard data |
| `/api/generation-history` | GET | — | `HistoryResponse` | Generation history |
| `/api/cities` | GET | — | `CityList` | List cities |

### Rules

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/rules` | GET | — | `RulesResponse` | Get scoring rules grouped by scope |
| `/api/rules` | PUT | `RulesUpdate` | `RulesResponse` | Bulk update rules (reordering) |
| `/api/rules` | POST | `{ rules: [...] }` | `RulesResponse` | Create rule(s) |
| `/api/rules/{id}` | PUT | `RuleUpdate` | `RulesResponse` | Update a single rule |
| `/api/rules/{id}` | DELETE | — | `RulesResponse` | Delete a rule |

Each rule has a single `priority` (0–100) used for list order, the severity
badge, and the LLM weight. Payload fields: `id`, `category`, `rule_type`,
`scope`, `key`, `value`, `description`, `priority`, `enabled`, `updated_at`.

- `PUT /api/rules/{id}` accepts any subset of `value`, `description`, `priority`,
  `enabled`, `scope`, `category`, `key`.
- `POST /api/rules` accepts `{ "rules": [ { scope, category, key, value, priority?, ... } ] }`.
- Reordering: the UI writes new `priority` values via `PUT /api/rules/{id}` (move
  up/down) or the bulk `PUT /api/rules` (drag-and-drop).

### WebSocket

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/ws` | WebSocket | Real-time event stream |

## WebSocket Protocol

### Connection

```javascript
const ws = new WebSocket(`ws://${host}/ws`);
```

### Client Events

```json
{"type": "watch", "room": "pending_123"}
{"type": "unwatch", "room": "pending_123"}
{"type": "cancel_job", "job_id": "abc-123"}
{"type": "reset_job", "job_id": "abc-123"}
```

### Server Events

```json
{"type": "execution:created", "room": "execution_123", "data": {...}}
{"type": "execution:started", "room": "execution_123", "data": {...}}
{"type": "execution:completed", "room": "execution_123", "data": {...}}
{"type": "execution:failed", "room": "execution_123", "data": {...}}
{"type": "execution:cancelled", "room": "execution_123", "data": {...}}
{"type": "workflow:step:started", "room": "execution_123", "data": {...}}
{"type": "workflow:step:completed", "room": "execution_123", "data": {...}}
{"type": "queue:entry:removed", "room": "execution_123", "data": {...}}
```

## SSE Endpoints

### Processing Events Stream

```
GET /events/processing
Accept: text/event-stream

event: execution.started
data: {"id": "abc-123", "type": "execution.started", "timestamp": "…",
       "job_id": null, "execution_id": "exec-1",
       "target_type": "company", "target_id": "8f5b1c2e-…",
       "payload": {"status": "RUNNING", "updated_at": "…", "target_type": "company", "target_id": "8f5b1c2e-…"}}
```

Every processing event carries `target_type` (`job` | `company`) and `target_id`
on both the envelope and the payload so subscribers can route events to the
right entity. See `docs/api/sse/processing-events.md` for the full event
catalogue.

## Authentication

### Current State

No authentication (single-user application).

### Future Considerations

```python
# When needed:
from fastapi import Depends, Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token=Depends(security)):
    return verify_token(token.credentials)

@router.get("/jobs")
async def list_jobs(user=Depends(get_current_user)):
    ...
```

## CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Rate Limiting

### Current State

No rate limiting (single-user application).

### Future Considerations

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.get("/jobs")
@limiter.limit("100/minute")
async def list_jobs(request: Request):
    ...
```
