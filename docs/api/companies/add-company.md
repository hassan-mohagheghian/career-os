# Add Company API

## Purpose

Creates a Company from intake (name + notes + links) and, when `queue` is true
(default), immediately queues it for processing through the shared
`COMPANY_PROCESSING` `ProcessingExecution` lifecycle.

This replaces the legacy `POST /api/pending-companies` intake.

---

# Endpoint

POST /api/companies

Returns `201 Created` on success.

---

# Request Body

```json
{
  "name": "Acme GmbH",
  "notes": [{ "content": "Berlin product company" }],
  "links": [{ "url": "https://acme.example", "title": "Website" }],
  "source": "web",
  "queue": true
}
```

| Field  | Type             | Required | Default | Description                                      |
| ------ | ---------------- | -------- | ------- | ------------------------------------------------ |
| name   | string           | No       | ""      | Company name. Fallback to a link/note URL when empty. |
| notes  | list of `{content}` | No     | []      | Text notes, stored as `note:` rows in `company_links`. |
| links  | list of `{url, title}` or strings | No | [] | URL links, stored as URL rows in `company_links`. Notes and links are kept as separate entities so context preparation can collect them as sources. |
| source | string           | No       | "web"   | Intake source label.                             |
| queue  | boolean          | No       | true    | When true, creates a `COMPANY_PROCESSING` execution and enqueues it. |

Empty body (`{}`) is valid — a company is created with a default name and queued.

---

# Response

```json
{
  "id": "019fd121-eac7-7537-aa3a-ddded8bb0cc8",
  "name": "Acme GmbH",
  "source": "web",
  "input_type": "url",
  "status": "queued",
  "execution_id": "exec-123",
  "created_at": "...",
  "updated_at": "..."
}
```

- `status` is `"queued"` when `queue: true` (an execution was created), or
  `"created"` when `queue: false`.
- `execution_id` is present only when `queue: true`.
- `id` is a UUID v7 string.

---

# Errors

400

Invalid request body.

500

Internal server error.

---

# Related Documents

- docs/api/companies/list-companies.md
- docs/api/companies/company-detail.md
- docs/api/companies/reprocess-company.md
- docs/ux/features/companies/add-company.md
- docs/domain/processing/processing-execution.md
