# Create Job API

## Purpose

Creates a new Job from a job posting URL.

By default the Job is stored in the Jobs list but is **not** automatically
added to the Processing Queue.

When the optional `queue` flag is set to `true`, the Job is created and
**immediately** follows the instant processing workflow — the same workflow
triggered by `POST /api/jobs/{job_id}/process`:

1. A `JOB_PROCESSING` ProcessingExecution is created.
2. The execution is marked `queued` and its task is enqueued on TaskIQ.
3. A TaskIQ worker runs the LangGraph job-processing workflow (fetch →
   extract → analyze → score → persist), streaming progress over SSE.

See:

- `docs/api/processing/process-job.md`
- `docs/workflows/job-processing.md`
- `docs/ux/flows/jobs/queue-job.md`

---

# Endpoint

```http
POST /api/jobs
```

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

```json
{
  "job_post_url": "https://company.com/jobs/backend-engineer",
  "job_title": "Senior Backend Engineer",
  "links": [
    {
      "title": "LinkedIn",
      "url": "https://linkedin.com/jobs/view/123456"
    },
    {
      "title": "Company Careers",
      "url": "https://company.com/careers/backend"
    }
  ],
  "notes": [
    {
      "title": "Requirements",
      "content": "Copied text from the job description..."
    },
    {
      "title": "Personal Notes",
      "content": "Interesting opportunity."
    }
  ],
  "queue": true
}
```

---

# Request Schema

| Field        | Type    | Required | Description                           |
| ------------ | ------- | -------- | ------------------------------------- |
| job_post_url | string  | Yes      | Primary job posting URL               |
| job_title    | string  | No       | Optional title.                       |
| links        | array   | No       | Additional reference links            |
| notes        | array   | No       | Additional notes                      |
| queue        | boolean | No       | Create and immediately queue for processing. Default `false`. |

---

## Link Object

| Field | Type   | Required |
| ----- | ------ | -------- |
| title | string | No       |
| url   | string | Yes      |

---

## Note Object

| Field   | Type   | Required |
| ------- | ------ | -------- |
| title   | string | No       |
| content | string | Yes      |

---

# Validation

## job_post_url

- Required
- Must be a valid URL

---

## job_title

- Optional

---

## links

For every item:

- URL is required
- Title is optional

---

## notes

For every item:

- Content is required
- Title is optional

---

## queue

- Optional
- Boolean
- `false` (default) → create only, no processing starts
- `true` → create and immediately queue for processing

---

# Success Response

## HTTP

```http
201 Created
```

---

## Body

Create without queue:

```json
{
  "id": "job_01JABCDEFG123456789",
  "status": "imported",
  "message": "Job created successfully.",
  "execution_id": null
}
```

Create & queue:

```json
{
  "id": "job_01JABCDEFG123456789",
  "status": "queued",
  "message": "Job created successfully.",
  "execution_id": "exec_01JABCDEFG987654321"
}
```

---

# Error Responses

## Validation Error

```http
400 Bad Request
```

Example

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "job_post_url is required."
  }
}
```

---

## Duplicate Job

```http
409 Conflict
```

Example

```json
{
  "error": {
    "code": "JOB_ALREADY_EXISTS",
    "message": "A Job with the same primary URL already exists."
  }
}
```

---

## Unauthorized

```http
401 Unauthorized
```

---

## Forbidden

```http
403 Forbidden
```

---

## Server Error

```http
500 Internal Server Error
```

---

# Side Effects

When the request succeeds **without** `queue`:

- A new Job is created.
- Status is set to **Imported**.
- The Job appears in the Jobs list.
- The Job is **not** added to the Processing Queue.
- No background processing starts.

When the request succeeds **with** `queue: true`:

- A new Job is created.
- Status is set to **Queued**.
- A `JOB_PROCESSING` ProcessingExecution is created and dispatched to the
  TaskIQ worker queue (`execution_id` is returned).
- The instant processing workflow starts: the worker runs fetch → extract →
  analyze → score → persist and streams progress over SSE.
- The Job appears in the Jobs list with status **Queued** and in the
  Processing Queue.

---

# Frontend Behavior

On success:

1. Close the Add Job Drawer.
2. Refresh the Jobs list.
3. Display the new Job.
4. When `queue` was requested, open the Processing Queue drawer so the user
   sees the live workflow progress immediately.
5. Optionally highlight the newly created Job.
6. Optionally show a success notification.

---

# Related Documents

- `docs/ux/features/jobs/add-job.md`
- `docs/ux/flows/jobs/create-job.md`
- `docs/ux/flows/jobs/queue-job.md`
- `docs/api/processing/process-job.md`
- `docs/workflows/job-processing.md`
