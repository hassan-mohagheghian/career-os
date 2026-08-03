# API Design

## Overview

This document defines the FastAPI API conventions, request/response patterns, and error handling for the Job Search Intelligence platform.

## Router Organization

Routes are organized by DDD bounded context. Each context owns its `presentation/api/` layer.

```python
# shared/presentation/api/root_router.py
from fastapi import APIRouter

api_router = APIRouter(prefix="/api")

api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(companies_router, prefix="/companies", tags=["companies"])
api_router.include_router(skills_router, prefix="/skills", tags=["skills"])
api_router.include_router(insights_router, prefix="/insights", tags=["insights"])
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(pending_router, prefix="/pending", tags=["pending"])
api_router.include_router(pending_companies_router, prefix="/pending-companies", tags=["pending-companies"])
api_router.include_router(skill_roadmaps_router, prefix="/skill-roadmaps", tags=["skill-roadmaps"])
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

# Example:
{
    "error": {
        "code": "NOT_FOUND",
        "message": "Job not found",
        "details": {"job_id": "8f5b1c2e-…"}
    }
}
```

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
| `/api/companies` | GET | — | `CompanyListResponse` | List companies |
| `/api/companies/{id}` | GET | — | `CompanyResponse` | Get company |
| `/api/companies` | POST | `CompanyCreate` | `CompanyResponse` | Create company |
| `/api/companies/{id}` | PUT | `CompanyUpdate` | `CompanyResponse` | Update company |
| `/api/companies/{id}` | DELETE | — | `{"success": true}` | Delete company |
| `/api/companies/{id}/intelligence` | GET | — | `CompanyIntelligenceResponse` | Get intelligence |
| `/api/companies/{id}/notes` | POST | `NoteCreate` | `NoteResponse` | Add note |
| `/api/companies/{id}/links` | POST | `LinkCreate` | `LinkResponse` | Add link |

### Pending (Job Queue)

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/pending` | GET | — | `PendingListResponse` | List pending jobs |
| `/api/pending` | POST | `PendingCreate` | `PendingResponse` | Queue new job |
| `/api/pending/{id}` | GET | — | `PendingResponse` | Get pending job |
| `/api/pending/{id}` | DELETE | — | `{"success": true}` | Cancel pending job |
| `/api/pending/{id}/reset` | POST | — | `PendingResponse` | Reset pending job |
| `/api/pending/stream` | GET | — | SSE stream | Real-time updates |
| `/api/pending/queue-all` | POST | — | `{"queued": N}` | Queue all pending |

### Pending Companies

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/pending-companies` | GET | — | `PendingCompanyListResponse` | List pending companies |
| `/api/pending-companies` | POST | `PendingCompanyCreate` | `PendingCompanyResponse` | Queue company |
| `/api/pending-companies/{id}` | GET | — | `PendingCompanyResponse` | Get pending company |
| `/api/pending-companies/{id}` | DELETE | — | `{"success": true}` | Cancel pending company |
| `/api/pending-companies/stream` | GET | — | SSE stream | Real-time updates |

### Skills

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/skills` | GET | — | `SkillListResponse` | List skills |
| `/api/skills` | POST | `SkillCreate` | `SkillResponse` | Create skill |
| `/api/skills/{id}` | PUT | `SkillUpdate` | `SkillResponse` | Update skill |
| `/api/skills/{id}` | DELETE | — | `{"success": true}` | Delete skill |
| `/api/skills/{id}/hide` | PATCH | — | `SkillResponse` | Soft-delete skill |
| `/api/skills/{id}/restore` | PATCH | — | `SkillResponse` | Restore hidden skill |
| `/api/skills/{id}/rename` | PATCH | `RenameSkill` | `SkillResponse` | Rename skill |
| `/api/skills/merge` | POST | `MergeSkills` | `SkillResponse` | Merge skills |
| `/api/skills/categories` | GET | — | `CategoryList` | List categories |
| `/api/skills/stats` | GET | — | `SkillStats` | Skill statistics |

### Skill Roadmaps

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/skill-roadmaps` | GET | — | `RoadmapListResponse` | List roadmaps |
| `/api/skill-roadmaps/{id}` | GET | — | `RoadmapResponse` | Get roadmap tree |
| `/api/skill-roadmaps` | POST | `RoadmapCreate` | `RoadmapResponse` | Create roadmap |
| `/api/skill-roadmaps/generate` | POST | `GenerateRoadmap` | `RoadmapResponse` | AI generate roadmap |
| `/api/skill-roadmaps/extend` | POST | `ExtendRoadmap` | `RoadmapResponse` | Extend roadmap |
| `/api/skill-roadmaps/finegrain` | POST | `FinegrainRoadmap` | `RoadmapResponse` | Fine-grain roadmap |
| `/api/skill-roadmaps/{id}/cancel` | POST | — | `{"success": true}` | Cancel generation |
| `/api/skill-roadmap-progress` | GET | — | `ProgressResponse` | All progress |
| `/api/skill-roadmap-progress/{id}` | GET | — | `ProgressDetail` | Skill progress |

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

### Resumes

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/resumes` | GET | — | `ResumeListResponse` | List resumes |
| `/api/resumes` | POST | `ResumeCreate` | `ResumeResponse` | Create resume |
| `/api/resumes/{id}` | GET | — | `ResumeResponse` | Get resume |
| `/api/resumes/{id}` | PUT | `ResumeUpdate` | `ResumeResponse` | Update resume |
| `/api/resumes/{id}` | DELETE | — | `{"success": true}` | Delete resume |
| `/api/resumes/{id}/generate-cover` | POST | `GenerateCover` | `CoverLetterResponse` | Generate cover letter |

### Dashboard

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/dashboard` | GET | — | `DashboardResponse` | Dashboard data |
| `/api/generation-history` | GET | — | `HistoryResponse` | Generation history |
| `/api/cities` | GET | — | `CityList` | List cities |

### Rules

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/rules` | GET | — | `RulesResponse` | Get scoring rules |
| `/api/rules` | PUT | `RulesUpdate` | `RulesResponse` | Update rules |

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
{"type": "pending:update", "room": "pending_123", "data": {...}}
{"type": "pending:log", "room": "pending_123", "data": {...}}
{"type": "pending:complete", "room": "pending_123", "data": {...}}
{"type": "pending:error", "room": "pending_123", "data": {...}}
{"type": "company:update", "room": "company_456", "data": {...}}
{"type": "generation:update", "room": "generation_789", "data": {...}}
{"type": "insights:progress", "room": "insights", "data": {...}}
```

## SSE Endpoints

### Pending Stream

```
GET /api/pending/stream
Accept: text/event-stream

event: pending:update
data: {"id": "abc-123", "step": "fetch", "status": "processing"}

event: pending:complete
data: {"id": "abc-123", "job_id": "8f5b1c2e-…"}
```

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
