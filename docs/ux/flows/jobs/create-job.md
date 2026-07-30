# Create Job Flow

## Purpose

This flow describes what happens when the user creates a new Job without immediately adding it to the Processing Queue.

The Job is imported into the system and becomes available in the Jobs list.

Processing does not start automatically.

---

# Trigger

User clicks

```
Create Job
```

from the **Add Job Drawer**.

See:

- `features/jobs/add-job.md`

---

# Preconditions

The form must be valid.

Required:

- Job Post URL

Optional:

- Job Title
- Additional Links
- Notes

---

# Flow

```text
Open Add Job Drawer

        │

        ▼

Fill Form

        │

        ▼

Click "Create Job"

        │

        ▼

Validate Form

        │

        ├─────────────── Invalid
        │
        │
        ▼
Show Validation Errors
Keep Drawer Open

        │

        ▼

Valid

        │

        ▼

Create Job

        │

        ▼

Store Job

        │

        ▼

Status = Imported

        │

        ▼

Close Drawer

        │

        ▼

Refresh Jobs List

        │

        ▼

Highlight New Job

        │

        ▼

Done
```

---

# Validation Rules

The following validations must succeed before creating the Job.

## Job Post URL

- Required
- Must be a valid URL

---

## Additional Links

For every additional link:

- URL is required
- Title is optional

---

## Notes

For every note:

- Content is required
- Title is optional

---

# Job Creation

When validation succeeds, the application creates a new Job.

The Job should contain:

- Primary Job Post URL
- Optional Job Title
- Additional Links
- Notes

---

# Initial Job State

After creation:

| Property            | Value    |
| ------------------- | -------- |
| Exists in Jobs List | Yes      |
| Added to Queue      | No       |
| Processing Started  | No       |
| Status              | Imported |

---

# UI Updates

After a successful creation:

- Close the Add Job Drawer.
- Refresh the Jobs list.
- Display the newly created Job.
- Highlight the new Job temporarily (optional).
- Show a success notification (optional).

The Processing Queue must remain unchanged.

---

# Validation Failure

If validation fails:

- Keep the Drawer open.
- Preserve all entered values.
- Display validation messages.
- Focus the first invalid field.

No Job is created.

---

# Server Failure

If the server returns an error:

- Keep the Drawer open.
- Preserve all entered values.
- Display an error notification.
- Allow the user to retry.

No Job is created.

---

# Cancellation

If the user clicks **Cancel**:

- Close the Drawer.
- Discard unsaved changes.
- Return to the Jobs page.

No Job is created.

---

# Result

The Job has been successfully imported into the system.

It is now available in the Jobs list and can later be:

- Queued
- Edited
- Deleted

Processing has not started.

---

# Related Documents

- `features/jobs/add-job.md`
- `flows/jobs/queue-job.md`
- `features/jobs/page.md`
