# Edit Job Flow

## Purpose

This flow describes what happens when the user edits a Job's core data from the Jobs page.

The user corrects or completes contextual fields, saves, and the row refreshes with the new values.

Processing is not started, stopped, or blocked by an edit.

---

# Trigger

User clicks

```
Edit
```

from the **Job Row** Actions column.

See:

- `features/jobs/edit-job.md`
- `features/jobs/job-row.md`

---

# Preconditions

The Job exists in the Jobs list.

No pre-conditions related to processing status are enforced.

---

# Flow

```text
Open Jobs Page

        │

        ▼

Click Edit on a Job Row

        │

        ▼

Open Edit Job Drawer

        │

        ▼

Load Job Detail

        │

        ▼

Prefill Form

        │

        ▼

Edit Fields

        │

        ▼

Click "Save"

        │

        ▼

Validate Form

        │

        ├───────────── Invalid

        │

        ▼

Show Validation Errors

Keep Drawer Open

Preserve Values

        │

        ▼

Valid

        │

        ▼

Persist Changes

        │

        ▼

Close Drawer

        │

        ▼

Refresh Job Row

        │

        ▼

Done
```

---

# Validation Rules

The following validations must succeed before saving.

## Job Post URL

- Required
- Must be a valid URL

## Other fields

- Optional
- Blank value clears the field (except URL)

---

# Save Behavior

- The Job record is updated with the changed fields.
- Fields not edited are left unchanged (partial update).
- Notes and Additional Links are updated when added, edited, or removed.
- The affected row refreshes.

---

# UI Updates

After a successful save:

- Close the Edit Job Drawer.
- Refresh the affected Job Row.
- Reflect updated Title, Company, Location, and contextual fields in the row.
- Invalidate the job detail cache so a reopened drawer shows the latest values.

---

# Validation Failure

If validation fails:

- Keep the Drawer open.
- Preserve all entered values.
- Display validation messages.
- Focus the first invalid field.

No changes are persisted.

---

# Server Failure

If the server returns an error:

- Keep the Drawer open.
- Preserve all entered values.
- Display an error notification.
- Allow the user to retry.

No changes are persisted.

---

# Cancellation

If the user clicks **Cancel** or **Close**:

- Close the Drawer.
- Discard unsaved changes.
- Return to the Jobs page.

No changes are persisted.

---

# Result

The Job's core data has been updated and is visible in the Jobs list.

---

# Related Documents

- `features/jobs/edit-job.md`
- `features/jobs/add-job.md`
- `features/jobs/job-row.md`
- `features/jobs/page.md`