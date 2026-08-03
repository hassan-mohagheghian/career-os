# Delete Job

## Purpose

The Delete Job action permanently removes a Job from the system, including all
of its related data (summary, resume, and processing executions).

Deletion is **hard and irreversible**. It is guarded by a destructive
confirmation dialog to prevent accidental removal.

---

# Related Page

Located in:

- `features/jobs/page.md`
- `features/jobs/job-row.md`

Triggered from the **Delete** action on a **Job Row**.

Related:

- `api/jobs/delete-job.md`
- `flows/jobs/delete-job.md`

---

# Trigger

The **Delete** action in the Job Row's Actions column. It is an icon-only button
(a trash icon) with a tooltip label of **Delete**.

Available for all processing statuses.

---

# User Goals

The user should be able to:

- Delete a job they no longer want to track
- Remove all associated processing data at once
- Confirm before anything is permanently deleted
- Cancel if they change their mind

---

# Confirmation Dialog

Clicking **Delete** opens a destructive confirmation dialog instead of deleting
immediately.

```text
┌──────────────────────────────────────────────────────────┐
│ Delete Job                                    [ Cancel ] │
│                                                          │
│ Permanently delete this job and all its processing  [x]  │
│ data?                                                   │
│                                                          │
│                                        [ Cancel ] [Delete]│
└──────────────────────────────────────────────────────────┘
```

- Title: *Delete Job*
- Message: *"Permanently delete this Job and all its processing data?"*
- Confirm button: **Delete** (destructive/danger styling)
- Cancel button: **Cancel**

The action proceeds only when the user confirms. Closing the dialog (Escape,
backdrop, or Cancel) aborts the deletion.

---

# States

## Idle

The Delete icon is part of the row's Actions column.

## Confirm

The confirmation dialog is open, waiting for the user.

## Deleting

While `DELETE /api/jobs/{job_id}` is in flight the request is awaited before
showing any result.

## Success

- A success toast is shown (*"Job deleted"*).
- Any open Details or Edit drawer for that Job is closed.
- The Job list is refreshed and the deleted Job disappears.

## Error

- An error toast is shown (*"Failed to delete job"*).
- The Job remains in the list.

---

# User Flow

```text
Open Jobs Page

↓

Click Delete on a Job Row

↓

Confirmation dialog opens

↓

Confirm Delete            (or Cancel -> abort)

↓

DELETE /api/jobs/{job_id}

↓

Job removed from list

↓

Success toast shown
```

---

# Accessibility

- Icon button has an accessible label ("Delete").
- The confirmation dialog is focus-trapped.
- Escape and the Cancel button abort deletion.
- The destructive action is clearly distinct from non-destructive actions.

---

# Related Documents

- `pages/jobs.md`
- `job-row.md`
- `design-system/dialog.md`
- `api/jobs/delete-job.md`
- `flows/jobs/delete-job.md`