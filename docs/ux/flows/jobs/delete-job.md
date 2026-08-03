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

On confirm, the frontend calls:

```http
DELETE /api/jobs/{job_id}
```

The server hard-deletes the Job and all related rows. Success returns
`204 No Content`.

### 5. Refresh

On success:

- A toast confirms the deletion.
- Any open drawer for that Job closes.
- The Jobs list is refreshed; the Job is gone.

---

## Outcomes

| Outcome  | Behavior                                                      |
| -------- | ------------------------------------------------------------- |
| Cancel   | Dialog closes, Job stays.                                     |
| Success  | `204`, Job removed from the list, success toast.              |
| Not found| `404`, error toast, Job stays if still present.               |
| Failure  | Error toast, Job stays.                                      |

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