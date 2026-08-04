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
| Execution Actions   | `/api/processing/executions/{id}/...`       | Start, cancel, retry, remove queue entry |
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

## Job Details + Analysis

`GET /api/jobs/{job_id}` returns the full job record plus the `analysis`
block produced by the Job Analysis phase:

```json
{
  "id": "…",
  "title": "Senior Backend Engineer",
  "company_name": "Acme Inc",
  "scores": { "overall": 79, "fit": 85, "success": 70 },
  "analysis": {
    "recommendation": "consider",
    "apply_reason": "Great role overall.",
    "scores_explanation": {
      "fit_factors": ["Python backend experience"],
      "success_factors": ["Senior level"],
      "concerns": ["No Kafka experience"]
    },
    "summary": { "summary": "…", "resume_fit": "…", "note": "…" },
    "skills": [{ "name": "Python", "category": "Language", "level": 4, "status": "matched", "evidence": "…" }],
    "insights": ["…"],
    "generated_at": "2026-08-03T12:00:00+00:00"
  },
  "latest_processing_execution": { "…": "…" },
  "description": "…"
}
```

- `analysis` is `null` until the analysis phase completes for the job.
- For jobs processed before the analysis phase existed, `analysis` is a
  backward-compatible block built from the legacy `jobs`/`summaries`
  projections (no `recommendation`, grade-derived `summary`).
- The frontend refetches this endpoint on `execution.completed` /
  `execution.failed` SSE events so results appear live in the Job Details drawer.

---

## Full Reference

For endpoint-by-endpoint documentation see `docs/api/api-design.md` (conventions) and the per-context docs under `docs/api/`.
- `docs/api/` — per-domain API specs (`jobs/`, `processing/`, `companies/`, `sse/`, ...)
