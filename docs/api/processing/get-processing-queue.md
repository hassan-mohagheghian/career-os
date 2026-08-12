# Get Processing Queue

## Purpose

This endpoint provides the current state of the Processing Queue.

The Processing Queue is a temporary execution view used by the frontend Drawer.

It does not own Jobs.

Jobs remain in the Jobs domain and the queue only represents active processing state.

---

# Endpoint

GET

/api/processing/queue

---

# Usage

Used by:

- Processing Queue Drawer.
- Job processing live view.
- Dashboard processing widgets.

Main usage flow:

1. User opens Processing Queue Drawer.
2. Frontend requests current queue state.
3. Backend returns active ProcessingExecutions.
4. Frontend subscribes to SSE events for live updates.

---

# Response

The response contains three sections:

- Processing
- Queued
- Failed

Rows whose `execution_type` belongs to a removed feature (e.g.
`application_preparation`) are safe: `from_dict` maps unknown types to a
non-dispatchable `legacy` marker instead of raising, and migration
`application_003_cleanup_preparation_executions` hard-deletes orphaned rows on
upgrade.

Example:

{
"processing": [],
"queued": [],
"failed": []
}

---

# Processing Section

Contains executions currently assigned to workers. The queue serves both Jobs
and Companies: each entry carries a `target_type` (`job` | `company`), and for
companies `title` is the company name while `url`/`links` may be null.

Example:

{
"processing": [
{
"execution_id": "exec_123",
"job_id": "job_123",
"target_type": "job",
"target_id": "job_123",
"title": "Senior Backend Engineer",
"url": "https://www.linkedin.com/jobs/view/1234567890123456",
"links": [
{ "title": "Company Website", "url": "https://acme.example.com/careers" }
],
"status": "processing",
"current_step": "fetch_content",
"progress": 60,
"started_at": "2026-08-01T10:00:00Z"
}
]
}

A company entry looks like:

{
"processing": [
{
"execution_id": "exec_789",
"job_id": "company-uuid",
"target_type": "company",
"target_id": "company-uuid",
"title": "Acme GmbH",
"url": null,
"links": [ { "title": "Website", "url": "https://acme.example.com" } ],
"status": "processing",
"current_step": "analyze",
"progress": 60,
"started_at": "2026-08-01T10:00:00Z"
}
]
}

Fields:

execution_id

The active ProcessingExecution identifier.

job_id

Legacy alias of the target identifier (kept for backward compatibility; prefer
`target_id`).

target_type

The processing target kind: `job` or `company`.

target_id

The identifier of the processing target — a Job id for jobs, a Company UUID for
companies.

title

Human readable title — Job title for jobs, company name for companies.

url

The target's primary URL when the execution targets a Job (or a company with a
website), otherwise null.

links

Related link items parsed from the target. Each item has an optional title and a
url. Empty when the target has no links.

status

Current execution status.

Possible values:

- processing
- completed
- failed
- cancelled

current_step

Current user-facing workflow step.

progress

Current workflow progress percentage.

started_at

Execution start time.

---

# Queued Section

Contains Jobs waiting for execution.

Example:

{
"queued": [
{
"execution_id": "exec_456",
"job_id": "job_456",
"target_type": "job",
"target_id": "job_456",
"title": "Python Developer",
"status": "queued",
"position": 2,
"waiting_reason": "waiting_for_worker"
}
]
}

Fields:

execution_id

Queue execution identifier.

job_id

Legacy alias of the target identifier (prefer `target_id`).

target_type

`job` or `company`.

target_id

Target identifier (Job id or Company UUID).

title

Job title or company name.

position

Current queue position.

waiting_reason

Reason why execution is waiting.

Possible values:

- waiting_for_worker
- scheduled_retry
- manual_pause

---

# Failed Section

Contains failed executions waiting for user action.

Example:

{
"failed": [
{
"execution_id": "exec_789",
"job_id": "job_789",
"title": "Frontend Engineer",
"status": "failed",
"error": "Failed to fetch source",
"failed_step": "fetch_content"
}
]
}

Fields:

execution_id

Failed execution identifier.

job_id

Legacy alias of the target identifier (prefer `target_id`).

target_type

`job` or `company`.

target_id

Target identifier (Job id or Company UUID).

title

Job title or company name.

error

Failure reason.

failed_step

Workflow step where failure happened.

---

# Sorting Rules

Processing:

Sorted by:

1. Started time ascending.

Queued:

Sorted by:

1. Queue position.

Failed:

Sorted by:

1. Last failure time descending.

---

# Empty Response

When there are no active executions:

{
"processing": [],
"queued": [],
"failed": []
}

Frontend displays:

No active processing jobs.

---

# Relationship With SSE

This endpoint provides the initial snapshot.

After loading:

Frontend subscribes to:

docs/api/sse/processing-events.md

The frontend should not poll this endpoint continuously.

Live updates are delivered through SSE.

---

# Error Responses

## Unauthorized

HTTP 401

## Forbidden

HTTP 403

## Server Error

HTTP 500

---

# Related Documents

- docs/api/sse/processing-events.md
- docs/api/processing/get-processing-execution.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/workflow-progress.md
- docs/ux/features/jobs/processing-queue.md
- docs/ux/flows/jobs/process-job-live.md
