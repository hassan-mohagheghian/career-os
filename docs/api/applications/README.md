# Applications API

## Purpose

The Applications API exposes the application record, its follow-ups, documents and
preparation plan, and queues AI generation of the application artifacts. It lives in
the Applications bounded context router (`/api/applications`) — per-context routers
(AGENTS.md rule 10).

## Overview

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/applications/by-job/{job_id}` | Application for a job (404 when none). |
| POST | `/api/applications` | Create an application for a job (default status `recommended`). |
| PATCH | `/api/applications/{application_id}` | Update `status` / `applied_at`. |
| POST | `/api/applications/{application_id}/follow-ups` | Add a follow-up. |
| PATCH | `/api/applications/follow-ups/{follow_up_id}` | Update a follow-up (date, note, completed). |
| DELETE | `/api/applications/follow-ups/{follow_up_id}` | Delete a follow-up (204). |
| POST | `/api/applications/{application_id}/preparation/generate` | Queue preparation generation (202). |
| POST | `/api/applications/{application_id}/documents/{document_type}/generate` | Queue document generation (202). |
| PATCH | `/api/applications/documents/{document_id}` | Edit document content. |
| DELETE | `/api/applications/documents/{document_id}` | Delete a document. |

## Get Application by Job

`GET /api/applications/by-job/{job_id}`

Returns the full application detail: core fields + `follow_ups`, `documents`,
`preparation`. `404` when the job has no application.

## Create Application

`POST /api/applications`  — body `{ "job_id": "..." }`

Creates the application with status `recommended`; returns the full detail (201).
The pipeline allows at most one application per job.

## Update Application

`PATCH /api/applications/{application_id}` — body `{ "status"?, "applied_at"? }`

Allows changing `status` (one of `recommended`, `preparing`, `ready_to_apply`,
`applied`, `rejected`, `withdrawn`) and `applied_at` (ISO date or `null` to clear).

## Follow-ups

- `POST /api/applications/{id}/follow-ups` — body `{ "scheduled_at"?, "note"? }`,
  returns the follow-up (201).
- `PATCH /api/applications/follow-ups/{follow_up_id}` — body `{ "scheduled_at"?,
  "note"?, "completed"? }`, returns the follow-up.
- `DELETE /api/applications/follow-ups/{follow_up_id}` — 204.

## Generation Endpoints

Both generation endpoints create a `ProcessingExecution` targeting the application
and dispatch it to the queue immediately, returning **202**:

```
POST /api/applications/{id}/preparation/generate
POST /api/applications/{id}/documents/{tailored_resume|cover_letter}/generate

Response 202: { "execution_id": "...", "status": "queued", "artifact": "..." }
```

Execution types: `application_preparation`, `application_resume`,
`application_cover_letter` (see `docs/ai/application-intelligence.md`). Progress is
streamed over SSE (`/events/processing`, `target_type="application"`); the client
refetches the application detail on completion/failure.

The pipeline enforces **at most one active execution per application** — a second
generate while one is queued/running returns **409 Conflict**.

## Documents

- `PATCH /api/applications/documents/{document_id}` — body `{ "content": "..." }`
  (markdown); bumps the version.
- `DELETE /api/applications/documents/{document_id}` — `{ "status": "deleted" }`.

## Errors

| Code | Condition |
| ---- | --------- |
| 400 | Invalid document type, empty required fields. |
| 404 | Application / document / follow-up not found; no application for job. |
| 409 | A generation execution is already active for the application. |
| 422 | Validation error (e.g. empty `job_id`). |

## Job Delete Cascade

Deleting a job (`DELETE /api/jobs/{job_id}`) hard-deletes the application, its
follow-ups, documents, preparations and the application's generation executions
(rule 8).

# Related Documents

- `docs/domain/applications/application.md`
- `docs/ai/application-intelligence.md`
- `docs/ux/features/applications/workspace.md`
