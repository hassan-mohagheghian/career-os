# List Jobs API

## Purpose

Returns a paginated list of Jobs for the Jobs page.

This endpoint is optimized for browsing, searching, filtering and sorting.

The endpoint is read-only.

Each row carries a small projection of the job's **latest processing execution**
(id, status, started/finished timestamps). Live, step-by-step progress is
retrieved separately through SSE.

A job that has never been processed has `latest_processing_execution` set to
`null` and `job_status` set to `null`. Processing status comes exclusively from
`processing_executions` — the legacy `jobs.status` column is not used by this
endpoint.

---

# Endpoint

GET /api/jobs

---

# Query Parameters

## Pagination

| Parameter | Type    | Required | Default |
| --------- | ------- | -------- | ------- |
| page      | integer | No       | 1       |
| page_size | integer | No       | 25      |

Maximum page_size is 100.

---

## Search

| Parameter | Type   |
| --------- | ------ |
| query     | string |

Search is performed against:

- Job title
- Company name
- Location
- Raw keywords

Search should be case-insensitive.

---

## Filters

### Processing Status

```text
processing_status=

queued
starting
running
completed
failed
cancelled
```

A job matches only when its **latest** execution (by `created_at`) has the given
status. Jobs with no execution are never returned by this filter, regardless of
the legacy `jobs.status` value.

---

### Processing Status

The `processing_status` filter above is the only status filter. The legacy
`jobs.status` values (`imported`, `processed`, `archived`) are not part of the
list model and cannot be filtered on here.

---

### Company

```text
company_id
```

---

### Location

```text
location
```

---

### Remote

```text
remote=true
```

---

### Visa

```text
visa=true
```

---

### Score Range

```text
overall_score_min

overall_score_max
```

---

## Sorting

Supported sort fields

```text
updated_at

created_at

overall_score

fit_score

success_score

company

title
```

Order

```text
asc

desc
```

---

# Response

```json
{
  "items": [
    {
      "id": "...",
      "title": "...",
      "company_name": "...",
      "location": "...",
      "remote": true,
      "visa_sponsorship": false,

      "job_status": "completed",

      "latest_processing_execution": {
        "id": "...",
        "status": "completed",
        "started_at": "...",
        "finished_at": "..."
      },

      "scores": {
        "overall": 91,
        "fit": 94,
        "success": 88
      },

      "updated_at": "...",
      "created_at": "..."
    }
  ],

  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_items": 523,
    "total_pages": 21
  }
}
```

---

# Returned Information

Each row should contain only the information required by the Jobs page.

Large objects must never be returned.

Excluded data includes:

- Raw HTML
- Parsed HTML
- Prompt history
- Recommendations
- Processing logs
- Timeline
- LLM output

Those are loaded by dedicated endpoints.

The job detail endpoint (`GET /api/jobs/{job_id}`) is the one that returns the
full analysis block, not this list:

```json
{
  "analysis": {
    "recommendation": "apply",
    "apply_reason": "...",
    "scores_explanation": {
      "fit_factors": ["..."],
      "success_factors": ["..."],
      "concerns": ["..."]
    },
    "summary": {
      "summary": "...",
      "resume_fit": "...",
      "note": "..."
    },
    "skills": [
      { "name": "Python", "category": "Language", "level": 4, "status": "matched", "evidence": "..." }
    ],
    "insights": ["..."],
    "generated_at": "..."
  }
}
```

For jobs processed before the analysis phase existed, the block is built from
the legacy `jobs`/`summaries` projections (no recommendation).

---

# Performance Requirements

The endpoint should support:

- Pagination
- Database indexes
- Efficient filtering
- Efficient sorting

The endpoint must not perform N+1 queries.

---

# Authorization

Users may only retrieve Jobs they own.

---

# Errors

400

Invalid query parameters.

401

Unauthorized.

403

Forbidden.

500

Internal server error.

---

# Related Documents

- docs/domain/jobs/job-search.md
- docs/ux/features/jobs/page.md
- docs/api/processing/process-job.md
