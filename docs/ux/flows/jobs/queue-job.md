# Queue Job Flow (Create & Queue)

## Purpose

This flow describes what happens when the user creates a new Job **and**
immediately adds it to the Processing Queue in a single action.

The Job is imported into the system and the instant processing workflow starts
without any extra click — the same workflow as pressing **Process** on an
existing job.

---

# Trigger

User clicks

```
Create & Queue
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

Click "Create & Queue"

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

Create ProcessingExecution
(JOB_PROCESSING, target = job)

        │

        ▼

Mark execution QUEUED

        │

        ▼

Enqueue TaskIQ task

        │

        ▼

Close Drawer
Refresh Jobs List

        │

        ▼

Status = Queued

        │

        ▼

Open Processing Queue drawer

        │

        ▼

TaskIQ worker receives task
(live progress over SSE)

        │

        ▼

LangGraph job-processing workflow
(fetch → extract → analyze → score → persist)

        │

        ▼

Status = Completed / Failed

        │

        ▼

Done
```

---

# Instant Processing Workflow

The **Create & Queue** action runs the exact same processing workflow as
`POST /api/jobs/{job_id}/process`:

1. **Create execution** — a `JOB_PROCESSING` ProcessingExecution is created for
   the new job id.
2. **Dispatch** — the execution is marked `queued` and its task is enqueued on
   TaskIQ.
3. **Run** — a TaskIQ worker executes the LangGraph job-processing workflow
   (context preparation → job analysis → scoring → persist).
4. **Stream** — progress is delivered live over SSE (`execution.created`,
   `workflow.step.*`, `execution.completed` / `execution.failed`).

The Processing Queue drawer and the Jobs list stay in sync via the shared SSE
event stream.

---

# Initial Job State

After creation:

| Property            | Value    |
| ------------------- | -------- |
| Exists in Jobs List | Yes      |
| Added to Queue      | Yes      |
| Processing Started  | Yes      |
| Status              | Queued   |

---

# UI Updates

After a successful **Create & Queue**:

- Close the Add Job Drawer.
- Refresh the Jobs list.
- Display the newly created Job with status **Queued**.
- Open the Processing Queue drawer to show the live workflow progress.
- Show a success notification.

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

No Job is created and nothing is queued.

---

# Cancellation

If the user clicks **Cancel**:

- Close the Drawer.
- Discard unsaved changes.
- Return to the Jobs page.

No Job is created.

---

# Result

The Job has been imported and is being processed.

It is visible in:

- The Jobs list (status **Queued**).
- The Processing Queue (live workflow progress).

---

# Related Documents

- `features/jobs/add-job.md`
- `flows/jobs/create-job.md`
- `flows/jobs/process-job-live.md`
- `api/jobs/create-job.md`
- `api/processing/process-job.md`
- `workflows/job-processing.md`
