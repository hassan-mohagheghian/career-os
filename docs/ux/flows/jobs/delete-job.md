# Delete Job Flow

## Purpose

Removes a Job and all of its related data (summary, resume, processing
executions) from the Jobs workspace.

This is a destructive, irreversible action. A confirmation step is required.

---

## Steps

### 1. Open Jobs Page

The user is on the Jobs page with jobs listed.

### 2. Choose a Job to Delete

The user clicks the Delete (trash) action on a Job Row.

### 3. Confirm

A destructive confirmation dialog appears:

- **Delete Job** — *Permanently delete this Job and all its processing data?*
- Buttons: Cancel / Delete

If the user cancels, nothing happens and the Job stays.

### 4. Delete on the Server

On confirm, the Job is removed from the list immediately via an **optimistic
cache update** and the frontend calls:

```http
DELETE /api/jobs/{job_id}
```

The server hard-deletes the Job and all related rows. Success returns
`204 No Content` (empty body, handled by the shared HTTP client without JSON
parsing).

### 5. Resolve

On success:

- The deleted Job stays gone from the list.
- A toast confirms the deletion.
- Any open drawer for that Job closes.
- The `jobs-v2-infinite` queries are invalidated, re-fetching pages from the
  server so pagination and totals stay correct.

On failure:

- The optimistic update is rolled back; the Job reappears in the list.
- An error toast is shown.

---

## Outcomes

| Outcome  | Behavior                                                      |
| -------- | ------------------------------------------------------------- |
| Cancel   | Dialog closes, Job stays.                                     |
| Success  | `204`, Job removed immediately (optimistic), success toast.   |
| Not found| `404`, rollback + error toast, Job stays if still present.    |
| Failure  | Rollback + error toast, Job stays.                           |

---

## Permissions / Guards

- No authentication required.
- Deleting is not blocked while a Job is processing; the execution is also
  removed.

---

## Related Documents

- `features/jobs/delete-job.md`
- `features/jobs/job-row.md`
- `api/jobs/delete-job.md`