# Delete Job API

## Purpose

Permanently (hard) deletes a Job and all of its related data. This is the
Delete Job feature.

Deletion is **hard**: the Job row is removed from the database along with any
summary, resume, and processing execution rows associated with the Job. This is
permanent and cannot be undone.

Deletion does not touch other Jobs.

---

# Endpoint

```http
DELETE /api/jobs/{job_id}
```

---

# Path Parameters

| Parameter | Type   | Description     |
| --------- | ------ | --------------- |
| job_id    | string | The Job's UUID. |

---

# Authentication

Authentication not required.

---

# Request

No body is required.

## Headers

```http
Content-Type: application/json
```

---

# Success Response

## HTTP

```http
204 No Content
```

No response body is returned.

---

# Error Responses

## Not Found

```http
404 Not Found
```

Returned when no Job exists with the given `job_id`.

```json
{
  "detail": "Job {job_id} not found"
}
```

## Server Error

```http
500 Internal Server Error
```

---

# Side Effects

When the request succeeds:

- The Job row is deleted.
- The canonical `job_analysis` row (schema `job`) for the Job is deleted.
- Related summary and resume rows (if any) are deleted.
- All processing executions targeting the Job are deleted.
- The job list cache is invalidated so the deleted Job disappears from the UI.

Deletion does not raise an error if there are no related rows to remove.

---

# Frontend Behavior

1. User clicks the Delete (trash) action on a Job Row.
2. A destructive confirmation dialog is shown: *"Permanently delete this job
   and all its processing data?"*.
3. On confirmation, `DELETE /api/jobs/{job_id}` is called.
4. On success a toast is shown, any open details/edit drawer for the Job is
   closed, and the Job list is refreshed.

---

# Related Documents

- `docs/ux/features/jobs/delete-job.md`
- `docs/api/jobs/edit-job.md`
- `docs/api/jobs/create-job.md`
- `docs/api/jobs/list-jobs.md`