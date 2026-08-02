# Edit Job API

## Purpose

Partially updates a Job's core data (Edit Job feature).

Unlike `POST /api/jobs`, editing is a **partial update**: fields omitted from
the request body are left unchanged. Notes and additional links can be added,
edited, and removed.

Editing does not start, stop, or block processing.

---

# Endpoint

```http
PATCH /api/jobs/{job_id}
```

---

# Path Parameters

| Parameter | Type   | Description      |
| --------- | ------ | ---------------- |
| job_id    | string | The Job's UUID.  |

---

# Authentication

Authentication not required.

---

# Request

## Headers

```http
Content-Type: application/json
```

---

## Body

All fields are optional.

```json
{
  "title": "Staff Software Engineer",
  "role": "Senior Backend Engineer",
  "company": "Acme GmbH",
  "location": "Berlin",
  "url": "https://company.com/jobs/backend-engineer",
  "work_type": "Hybrid",
  "employment_type": "Full-time",
  "visa": "Strong",
  "salary": "€90k - €110k",
  "description": "Work alongside a cross-functional team...",
  "notes": [
    {
      "title": "Requirements",
      "content": "Must know Python and Postgres."
    }
  ],
  "links": [
    {
      "title": "Company Careers",
      "url": "https://company.com/careers/backend"
    }
  ]
}
```

---

# Request Schema

| Field           | Type   | Editable |
| --------------- | ------ | -------- |
| title           | string | Yes      |
| role            | string | Yes      |
| company         | string | Yes      |
| location        | string | Yes      |
| url             | string | Yes      |
| work_type       | string | Yes      |
| employment_type | string | Yes      |
| visa            | string | Yes      |
| salary          | string | Yes      |
| description     | string | Yes      |
| notes           | array  | Yes      |
| links           | array  | Yes      |

Fields not listed (e.g. `status`, `scores`, `created_at`) are not editable and
are ignored.

---

## Note Object

| Field   | Type   | Required |
| ------- | ------ | -------- |
| title   | string | No       |
| content | string | Yes      |

---

## Link Object

| Field | Type   | Required |
| ----- | ------ | -------- |
| title | string | No       |
| url   | string | Yes      |

---

# Validation

## url

- Optional, but if provided must start with `http://` or `https://`.
- Invalid URLs return `422 Unprocessable Entity`.

## notes / links

- Optional.
- Passing an empty array clears the existing list.
- Every link `url` must start with `http://` or `https://` or the request
  returns `422 Unprocessable Entity`.

## Other fields

- Optional.
- Blank values clear the field.

---

# Success Response

## HTTP

```http
200 OK
```

## Body

Returns the updated `JobDetail`.

```json
{
  "id": "8f5b1c2e-...",
  "num": 12,
  "title": "The Software Engineer",
  "company_name": "Acme GmbH",
  "role": "Senior Backend Engineer",
  "location": "Berlin",
  "work_type": "Hybrid",
  "employment_type": "Full-time",
  "salary": "€90k - €110k",
  "visa": "Strong",
  "url": "https://company.com/jobs/backend-engineer",
  "status": "imported",
  "scores": { "overall": 90, "fit": 85, "success": 88 },
  "description": "Work alongside a cross-functional team...",
  "notes": [{ "content": "Know Python and Postgres." }],
  "links": [{ "title": "Company Careers", "url": "https://company.com/careers/backend" }],
  "updated_at": "2026-08-02T10:00:00",
  "created_at": "2026-08-01T09:00:00"
}
```

Notes and links are returned as arrays (not raw JSON strings).

---

# Error Responses

## Not Found

```http
404 Not Found
```

Returned when no Job exists with the given `job_id`.

## Validation Error

```http
422 Unprocessable Entity
```

Returned when `url` or any link URL is invalid.

Example

```json
{
  "detail": "1 validation error for UpdateJobRequest ..."
}
```

## Server Error

```http
500 Internal Server Error
```

---

# Side Effects

When the request succeeds:

- The Job fields are updated in place.
- Omitted fields are preserved.
- Notes and links (when provided) replace the previous lists.
- The job detail cache is invalidated so a reopened Edit drawer shows the latest values.
- No processing is started or cancelled.

---

# Frontend Behavior

On success:

1. Close the Edit Job Drawer.
2. Refresh the affected Job Row.
3. Invalidate the job detail cache.

---

# Related Documents

- `docs/ux/features/jobs/edit-job.md`
- `docs/ux/flows/jobs/edit-job.md`
- `docs/api/jobs/create-job.md`
- `docs/api/jobs/list-jobs.md`