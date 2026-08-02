# API Overview

REST API served by FastAPI on port 5000. All endpoints return JSON. Real-time processing updates are delivered through Server-Sent Events (SSE).

**Base URL**: `http://localhost:5000`

**Interactive docs**: Swagger UI `/api/docs/`, ReDoc `/api/redoc/`, OpenAPI spec `/api/openapi.json`

---

## Quick Reference

| Group               | Base Path                                   | Purpose                               |
| ------------------- | ------------------------------------------- | ------------------------------------- |
| Jobs                | `/api/jobs`                                 | List, create, update, delete jobs     |
| Processing          | `/api/jobs/{job_id}/process`                | Start a Processing Execution          |
| Processing Queue    | `/api/processing/queue`                     | Snapshot of active executions         |
| Execution Detail    | `/api/processing/executions/{execution_id}` | Execution status + workflow progress  |
| Execution Actions   | `/api/processing/executions/{id}/...`       | Cancel, retry, remove queue entry     |
| Companies           | `/api/companies`                            | Company intelligence CRUD             |
| Skills              | `/api/tech-stack`                           | Skill management + aliases + merge    |
| Skill Roadmaps      | `/api/skill-roadmaps`                       | AI learning roadmaps + progress       |
| Insights            | `/api/insights`                             | Career intelligence sections          |
| Resumes             | `/api/resumes`                              | Resume / cover letter generation      |
| Rules               | `/api/rules`                                | Scoring rules configuration           |
| SSE                | `/api/sse/processing-events`                | Real-time processing event stream     |
| System              | `/api/generation-history`, `/api/health`    | History + health check                |

---

## Authentication

None. All endpoints are publicly accessible.

## Errors

All errors return JSON with the appropriate HTTP status (400, 404, 409, 500):

```json
{ "error": "<message>" }
```

## Versioning

No explicit API versioning. Breaking changes are avoided by maintaining backward compatibility.

---

## Full Reference

For endpoint-by-endpoint documentation see `docs/api/api-design.md` (conventions) and the per-context docs under `docs/api/`.
- `docs/api/` — per-domain API specs (`jobs/`, `processing/`, `companies/`, `sse/`, ...)
