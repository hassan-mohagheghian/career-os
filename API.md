# API Overview

REST API served by FastAPI on port 5000. All endpoints return JSON. Real-time processing updates are delivered through Server-Sent Events (SSE).

**Base URL**: `http://localhost:5000`

**Interactive docs**: Swagger UI `/api/docs/`, ReDoc `/api/redoc/`, OpenAPI spec `/api/openapi.json`

---

## Quick Reference

| Group               | Base Path                                   | Purpose                               |
| ------------------- | ------------------------------------------- | ------------------------------------- |
| Jobs                | `/api/jobs`                                 | List, create, update, delete, pin jobs |
| Processing          | `/api/jobs/{job_id}/process`                | Start a Processing Execution          |
| Processing Queue    | `/api/processing/queue`                     | Snapshot of active executions         |
| Execution Detail    | `/api/processing/executions/{execution_id}` | Execution status + workflow progress  |
| Execution Actions   | `/api/processing/executions/{id}/...`       | Start, cancel, retry, remove queue entry |
| Companies           | `/api/companies`                            | Company intelligence CRUD             |
| Skills              | `/api/tech-stack`                           | Skill management + aliases + merge    |
| Skill Roadmaps      | `/api/skill-roadmaps`                       | AI learning roadmaps + progress       |
| Insights            | `/api/insights`                             | Career intelligence sections          |
| Resumes             | `/api/resumes`                              | Resume / cover letter generation      |
| LinkedIn Profiles   | `/api/linkedin`                             | Versioned LinkedIn profile upload/list/delete |
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

## Pinned

Each job carries a user-managed `pinned` flag (`true`/`false`). It is managed
exclusively through its own endpoint and is **not** part of the edit-job
payload.

### `GET /api/jobs/list?pinned=true`

Restricts the jobs list to pinned jobs. Omitted (or `false`) returns all
jobs. Each list item exposes the `pinned` flag plus a lightweight
`recommendation` field (`apply` / `consider` / `skip`, `null` without a
completed analysis) — the full analysis block stays on the detail endpoint.

The list also supports `recommendation=apply|consider|skip` to filter to jobs
whose analysis produced that recommendation (jobs without analysis never
match).

### `PUT /api/jobs/{job_id}/pinned`

Request: `{ "pinned": true }` → Response `200`: `{ "pinned": true }`, or
`404` when the job is unknown.

---

## Profile Documents (Resume + LinkedIn)

Both the latest resume and the latest LinkedIn profile are fed into job
analysis as labeled extra context. The resume is authoritative for skills and
seniority; LinkedIn supplements it. "Latest" is the highest `version`.

### `POST /api/resumes` — upload a master resume

Request: `{ "raw_text": "…", "title": "Optional" }` (a legacy `content` key is
also accepted).

Response `200`: `{ "status": "saved", "version": 1, "id": "original_1" }`.

PII (name line, phone, email, LinkedIn/GitHub URLs) is masked before saving;
the row stores the masked `raw_text` plus an HTML `content` preview.

### `DELETE /api/resumes/{id}` — delete a resume

Response `200`: `{ "status": "deleted", "id": "original_1" }`, or `404` when the
id is unknown.

### `GET /api/linkedin` — list LinkedIn profiles

Returns all `linkedin_*` rows, newest version first.

### `POST /api/linkedin` — upload a LinkedIn profile

Request: `{ "raw_text": "…" }`. Response `200`:
`{ "status": "saved", "version": 1, "id": "linkedin_1" }`.

### `GET /api/linkedin/{id}` — get a LinkedIn profile

Returns the row, or `404` when unknown.

### `DELETE /api/linkedin/{id}` — delete a LinkedIn profile

Response `200`: `{ "status": "deleted", "id": "linkedin_1" }`, or `404`.

---

## Full Reference

For endpoint-by-endpoint documentation see `docs/api/api-design.md` (conventions) and the per-context docs under `docs/api/`.
- `docs/api/` — per-domain API specs (`jobs/`, `processing/`, `companies/`, `sse/`, ...)
