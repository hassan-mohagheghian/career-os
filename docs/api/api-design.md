# API Design

## Overview

This document defines the FastAPI API conventions, versioning strategy, request/response patterns, and error handling for the Job Search Intelligence platform.

## API Versioning

### URL-Based Versioning

```
/api/v1/jobs
/api/v1/companies
/api/v2/jobs  (future)
```

### Router Organization

```python
# api/router.py
from fastapi import APIRouter
from app.server.api.v1 import jobs, companies, skills, insights, resumes

api_router = APIRouter(prefix="/api")

api_router.include_router(jobs.router, prefix="/v1", tags=["jobs"])
api_router.include_router(companies.router, prefix="/v1", tags=["companies"])
api_router.include_router(skills.router, prefix="/v1", tags=["skills"])
api_router.include_router(insights.router, prefix="/v1", tags=["insights"])
api_router.include_router(resumes.router, prefix="/v1", tags=["resumes"])
```

## Request Validation

### Pydantic Models

```python
# api/v1/jobs.py
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

@router.get("/jobs/{num}")
async def get_job(
    num: int = Path(..., description="Job number", ge=1),
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
    num: int
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
        "details": {"job_num": 123}
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
| `/api/v1/jobs` | GET | — | `JobListResponse` | List jobs (paginated) |
| `/api/v1/jobs/{num}` | GET | — | `JobResponse` | Get job by number |
| `/api/v1/jobs` | POST | `JobCreate` | `JobResponse` | Create new job |
| `/api/v1/jobs/{num}` | PUT | `JobUpdate` | `JobResponse` | Update job |
| `/api/v1/jobs/{num}` | DELETE | — | `{"success": true}` | Delete job |
| `/api/v1/jobs/{num}/requeue` | POST | — | `{"success": true}` | Re-queue for processing |
| `/api/v1/jobs/{num}/rescore` | POST | — | `JobResponse` | Rescore existing job |

### Companies

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/v1/companies` | GET | — | `CompanyListResponse` | List companies |
| `/api/v1/companies/{id}` | GET | — | `CompanyResponse` | Get company |
| `/api/v1/companies` | POST | `CompanyCreate` | `CompanyResponse` | Create company |
| `/api/v1/companies/{id}` | PUT | `CompanyUpdate` | `CompanyResponse` | Update company |
| `/api/v1/companies/{id}` | DELETE | — | `{"success": true}` | Delete company |
| `/api/v1/companies/{id}/intelligence` | GET | — | `CompanyIntelligenceResponse` | Get intelligence |
| `/api/v1/companies/{id}/notes` | POST | `NoteCreate` | `NoteResponse` | Add note |
| `/api/v1/companies/{id}/links` | POST | `LinkCreate` | `LinkResponse` | Add link |

### Pending (Job Queue)

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/v1/pending` | GET | — | `PendingListResponse` | List pending jobs |
| `/api/v1/pending` | POST | `PendingCreate` | `PendingResponse` | Queue new job |
| `/api/v1/pending/{id}` | GET | — | `PendingResponse` | Get pending job |
| `/api/v1/pending/{id}` | DELETE | — | `{"success": true}` | Cancel pending job |
| `/api/v1/pending/{id}/reset` | POST | — | `PendingResponse` | Reset pending job |
| `/api/v1/pending/stream` | GET | — | SSE stream | Real-time updates |
| `/api/v1/pending/queue-all` | POST | — | `{"queued": N}` | Queue all pending |

### Pending Companies

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/v1/pending-companies` | GET | — | `PendingCompanyListResponse` | List pending companies |
| `/api/v1/pending-companies` | POST | `PendingCompanyCreate` | `PendingCompanyResponse` | Queue company |
| `/api/v1/pending-companies/{id}` | GET | — | `PendingCompanyResponse` | Get pending company |
| `/api/v1/pending-companies/{id}` | DELETE | — | `{"success": true}` | Cancel pending company |
| `/api/v1/pending-companies/stream` | GET | — | SSE stream | Real-time updates |

### Skills

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/v1/skills` | GET | — | `SkillListResponse` | List skills |
| `/api/v1/skills` | POST | `SkillCreate` | `SkillResponse` | Create skill |
| `/api/v1/skills/{id}` | PUT | `SkillUpdate` | `SkillResponse` | Update skill |
| `/api/v1/skills/{id}` | DELETE | — | `{"success": true}` | Delete skill |
| `/api/v1/skills/{id}/hide` | PATCH | — | `SkillResponse` | Soft-delete skill |
| `/api/v1/skills/{id}/restore` | PATCH | — | `SkillResponse` | Restore hidden skill |
| `/api/v1/skills/{id}/rename` | PATCH | `RenameSkill` | `SkillResponse` | Rename skill |
| `/api/v1/skills/merge` | POST | `MergeSkills` | `SkillResponse` | Merge skills |
| `/api/v1/skills/categories` | GET | — | `CategoryList` | List categories |
| `/api/v1/skills/stats` | GET | — | `SkillStats` | Skill statistics |

### Skill Roadmaps

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/v1/skill-roadmaps` | GET | — | `RoadmapListResponse` | List roadmaps |
| `/api/v1/skill-roadmaps/{id}` | GET | — | `RoadmapResponse` | Get roadmap tree |
| `/api/v1/skill-roadmaps` | POST | `RoadmapCreate` | `RoadmapResponse` | Create roadmap |
| `/api/v1/skill-roadmaps/generate` | POST | `GenerateRoadmap` | `RoadmapResponse` | AI generate roadmap |
| `/api/v1/skill-roadmaps/extend` | POST | `ExtendRoadmap` | `RoadmapResponse` | Extend roadmap |
| `/api/v1/skill-roadmaps/finegrain` | POST | `FinegrainRoadmap` | `RoadmapResponse` | Fine-grain roadmap |
| `/api/v1/skill-roadmaps/{id}/cancel` | POST | — | `{"success": true}` | Cancel generation |
| `/api/v1/skill-roadmap-progress` | GET | — | `ProgressResponse` | All progress |
| `/api/v1/skill-roadmap-progress/{id}` | GET | — | `ProgressDetail` | Skill progress |

### Insights

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/v1/insights` | GET | — | `InsightsResponse` | Get all insights |
| `/api/v1/insights/{section}` | GET | — | `SectionResponse` | Get section |
| `/api/v1/insights/refresh` | POST | — | `{"status": "started"}` | Generate all sections |
| `/api/v1/insights/{section}/refresh` | POST | — | `{"status": "started"}` | Generate section |
| `/api/v1/insights/progress` | GET | — | `ProgressResponse` | Generation progress |
| `/api/v1/insights/status` | GET | — | `StatusResponse` | Section statuses |
| `/api/v1/insights/skills-intel` | GET | — | `SkillsIntelResponse` | Skills intelligence |
| `/api/v1/insights/cancel` | POST | — | `{"success": true}` | Cancel generation |

### Resumes

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/v1/resumes` | GET | — | `ResumeListResponse` | List resumes |
| `/api/v1/resumes` | POST | `ResumeCreate` | `ResumeResponse` | Create resume |
| `/api/v1/resumes/{id}` | GET | — | `ResumeResponse` | Get resume |
| `/api/v1/resumes/{id}` | PUT | `ResumeUpdate` | `ResumeResponse` | Update resume |
| `/api/v1/resumes/{id}` | DELETE | — | `{"success": true}` | Delete resume |
| `/api/v1/resumes/{id}/generate-cover` | POST | `GenerateCover` | `CoverLetterResponse` | Generate cover letter |

### Dashboard

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/v1/dashboard` | GET | — | `DashboardResponse` | Dashboard data |
| `/api/v1/generation-history` | GET | — | `HistoryResponse` | Generation history |
| `/api/v1/cities` | GET | — | `CityList` | List cities |

### Rules

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/api/v1/rules` | GET | — | `RulesResponse` | Get scoring rules |
| `/api/v1/rules` | PUT | `RulesUpdate` | `RulesResponse` | Update rules |

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
GET /api/v1/pending/stream
Accept: text/event-stream

event: pending:update
data: {"id": "abc-123", "step": "fetch", "status": "processing"}

event: pending:complete
data: {"id": "abc-123", "num": 456}
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
