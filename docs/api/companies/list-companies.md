# List Companies API

## Purpose

Returns a paginated list of Companies for the Companies page.

This endpoint is optimized for browsing, searching, filtering and sorting.

The endpoint is read-only.

Scores are exposed as **raw values from the legacy scores blob** (they are
stored as numbers and may be fractional, e.g. `38.5`). The overall grade is the
company's `overall_grade`, falling back to `fit_grade` when the former is empty.

> Company processing is **legacy**: `pending_companies` + `enqueue_company_sync`
> + the LangGraph company graph. Unlike Jobs, there is no
> Processing-Execution/SSE model. Processing state is monitored through the
> pending-companies endpoint (polled by the Company Queue drawer).

---

# Endpoint

GET /api/companies/list

---

# Query Parameters

## Pagination

The list uses **cursor-based** pagination (keyset). There is no page number.

| Parameter | Type   | Required | Default |
| --------- | ------ | -------- | ------- |
| cursor    | string | No       | null    |
| page_size | integer| No       | 25      |

Maximum page_size is 100.

The first page is requested without a cursor. Each response returns the
`next_cursor` to pass for the next page.

---

## Search

| Parameter | Type   |
| --------- | ------ |
| query     | string |

Search is performed against:

- Company name
- Industry
- City
- Country
- Description

Search is case-insensitive.

---

## Filters

### Industry

```text
industry=Software Development
```

Exact match on the company's industry value.

---

## Sorting

Supported sort fields

```text
created_at

updated_at

name

overall_score

fit_score

success_score
```

Default sort is `created_at desc` (newest first, matching the repo-wide rule).

Every sort follows a **NULLS LAST** policy: rows where the sort column is `NULL`
(for example a company that has not been scored yet) always sort **after** rows
with a value, in both `asc` and `desc` order.

Score sorts (`overall_score`, `fit_score`, `success_score`) read the
corresponding key from the company's scores blob (`company_overall_score`,
`company_fit_score`, `company_success_score`).

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
      "name": "...",
      "logo_url": "...",
      "industry": "...",
      "city": "...",
      "country": "...",
      "company_size": "...",
      "company_type": "...",
      "website": "...",
      "linkedin_url": "...",
      "jobs_count": 12,
      "grade": "A+",
      "scores": {
        "overall": 88,
        "fit": 85,
        "success": 90
      },
      "status": "processed",
      "updated_at": "...",
      "created_at": "..."
    }
  ],
  "next_cursor": "...",
  "has_more": true,
  "total_count": 128,
  "loaded_count": 25
}
```

---

# Returned Information

Each row contains only the information required by the Companies page.

Large objects must never be returned.

Excluded data includes:

- Raw/parsed HTML
- Notes
- Links
- Intelligence payloads
- Score explanation / factors / prompts
- Processing logs / history

Those are loaded by a single detail endpoint: `GET /api/companies/list/{id}`,
which returns the company plus its notes, links, intelligence, scores and jobs
in one payload.

The only score-derived values exposed on the list are the lightweight `grade`
and the three `scores` values, batch-loaded per page (no N+1). Companies
without intelligence return `grade = null` and null scores.

---

# Performance Requirements

The endpoint should support:

- Keyset pagination (indexed on the sort column + id)
- Database indexes
- Efficient filtering
- Efficient sorting

The endpoint must not perform N+1 queries. `jobs_count` is aggregated in the
same query (filtering `JobModel.deleted == 0`).

---

# Authorization

Users may only retrieve Companies they own.

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

- docs/ux/features/companies/page.md
- docs/ux/features/companies/company-row.md
- docs/ux/flows/companies/browse-companies.md
