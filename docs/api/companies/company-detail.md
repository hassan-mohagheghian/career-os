# Company Detail API

## Purpose

Returns a single Company with **all** related information in one payload:

- Base profile fields (name, industry, location, size, website, description, ...)
- Processing status (`status`, `current_node`, `progress_pct`, `error`)
- Original notes
- Company links
- Intelligence analysis (`overview`, `culture_analysis`, ...)
- Scores (`fit`, `success`, `overall`, `overall_grade`)
- Linked jobs (slim projection)
- `job_count`

This mirrors the Jobs v2 detail pattern: the drawer fetches once and every tab
reads from the same payload. No separate `/links`, `/jobs` or local-history
calls are needed for the Company detail drawer.

> Company processing is **legacy**: `pending_companies` + `enqueue_company_sync`
> + the LangGraph company graph. Unlike Jobs, there is no
> Processing-Execution/SSE model. Processing state is exposed here via the
> `status` / `current_node` / `progress_pct` fields and monitored live through
> the pending-companies endpoint (polled by the Company Queue drawer).

---

# Endpoint

GET /api/companies/list/{id}

The route is registered on the companies v2 router, which is mounted **before**
the legacy companies router, so it shadows the legacy `GET /api/companies/{id}`
for the same path.

`{id}` is a **UUID v7 string** (e.g. `019fd121-eac7-7537-aa3a-ddded8bb0cc8`).

---

# Response

```json
{
  "id": "019fd121-eac7-7537-aa3a-ddded8bb0cc8",
  "name": "Example GmbH",
  "website": "https://...",
  "domain": "example.com",
  "industry": "Software Development",
  "country": "Germany",
  "city": "Berlin",
  "description": "...",
  "company_size": "51-200",
  "company_type": "PRODUCT_COMPANY",
  "logo_url": "https://...",
  "founded_year": "2015",
  "job_count": 3,
  "status": "processed",
  "current_node": "completed",
  "progress_pct": 100.0,
  "error": null,
  "notes": [
    { "id": 12, "content": "Great culture", "created_at": "..." }
  ],
  "links": [
    {
      "id": 7,
      "url": "https://...",
      "title": "LinkedIn",
      "description": "...",
      "status": "processed",
      "created_at": "..."
    }
  ],
  "intelligence": {
    "overview": { "founded": "2015", "headquarters": "Berlin" },
    "culture_analysis": {},
    "international_analysis": {},
    "career_analysis": {},
    "benefits_analysis": {},
    "visa_analysis": {},
    "technology_analysis": {},
    "recommendation": null,
    "scores": {
      "company_fit_score": 88,
      "company_success_score": 87,
      "company_overall_score": 88,
      "overall_grade": "A+"
    },
    "generated_at": "..."
  },
  "scores": {
    "overall": 88.0,
    "fit": 88.0,
    "success": 87.0,
    "overall_grade": "A+"
  },
  "jobs": [
    {
      "id": "019fd122-...",
      "role": "Principal Python Engineer",
      "location": "Berlin",
      "match": "...",
      "score": "A",
      "fit_score": 90,
      "success_score": 85,
      "overall_score": 88
    }
  ],
  "created_at": "...",
  "updated_at": "..."
}
```

---

# Notes

Notes are stored as `company_links` rows whose `title` starts with `note:`.
The detail endpoint returns them parsed as `{ id, content }` (the `note:`
prefix is stripped). Non-note links are returned under `links`.

---

# Errors

404

Company not found for the given id.

500

Internal server error.

---

# Related Documents

- docs/api/companies/list-companies.md
- docs/ux/features/companies/company-detail.md
- docs/ux/flows/companies/browse-companies.md
