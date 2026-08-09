# Delete Job API

## Purpose

Permanently (hard) deletes a Job and all of its related data. This is the
Delete Job feature.

Deletion is **hard**: the Job row is removed from the database along with its
`job_analysis` row, summary, and processing execution rows associated with the
Job. This is permanent and cannot be undone.

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

No response body is returned. Because the body is empty, the frontend HTTP
client resolves the request as `undefined` and **must not** try to parse a JSON
body (parsing an empty body raises a `SyntaxError`). This contract applies to
every `204` endpoint in the API.

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
- The related summary row (if any) is deleted.
- All processing executions targeting the Job are deleted.
- The frontend cache is updated so the deleted Job disappears from the UI.

Deletion does not raise an error if there are no related rows to remove.

---

# Frontend Behavior

The Delete Job action follows an **optimistic update** pattern so the Job
disappears from the list immediately after confirmation:

1. User clicks the Delete (trash) action on a Job Row.
2. A destructive confirmation dialog is shown: *"Permanently delete this job
   and all its processing data?"*.
3. On confirmation, the Job is removed from the React Query cache right away
   (`useJobsInfiniteQuery.deleteMutation`):
   - The Job is filtered out of every loaded page.
   - `total_items` is decremented on each page.
   - The previous cache state is snapshotted for rollback.
4. `DELETE /api/jobs/{job_id}` is sent. The response is `204 No Content`.
5. On success a toast is shown and any open details/edit drawer for the Job is
   closed.
6. The `jobs-v2-infinite` queries are invalidated, re-fetching the pages from
   the server so pagination/cursors stay consistent.
7. On failure the snapshot is restored (the Job reappears) and an error toast
   is shown.

The `204` empty-body response is handled by the shared HTTP client
(`apps/frontend/src/shared/api/http-client.ts`), which resolves empty success
responses to `undefined` instead of parsing a JSON body.

---

# Related Documents

- `docs/ux/features/jobs/delete-job.md`
- `docs/api/jobs/edit-job.md`
- `docs/api/jobs/create-job.md`
- `docs/api/jobs/list-jobs.md`