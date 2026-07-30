# Processing Queue

## Purpose

The Processing Queue provides a real-time view of Jobs that are currently being processed or waiting to be processed.

It is a temporary execution view and **does not own the Jobs**.

Jobs always remain in the Jobs list. The Processing Queue only reflects their current processing state.

The queue allows users to:

- Monitor background processing.
- Track processing progress.
- Manage queued Jobs.
- Retry failed Jobs.
- Cancel running Jobs.

---

# Related Page

Opened from:

- `docs/ux/features/jobs/page.md`

Uses:

- `docs/ux/design-system/drawer.md`

Related Flows:

- `docs/ux/flows/jobs/create-and-queue-job.md`
- `docs/ux/flows/jobs/retry-job.md`
- `docs/ux/flows/jobs/cancel-job.md`

---

# Container

Current implementation:

- Drawer

Future implementations may include:

- Split View
- Side Panel

The behavior defined in this document is independent of the container type.

---

# Drawer

Variant

- `lg`

Placement

- `right`

---

# Concept

The Processing Queue is **not** the Jobs list.

Jobs always exist in the Jobs list.

The Queue only contains temporary processing entries.

```text
Jobs List
────────────────────────────────────────

Senior Backend Engineer      Imported

Python Developer            Queued

Staff Engineer              Processing

Frontend Engineer           Failed

Data Engineer               Processed


Processing Queue
────────────────────────────────────────

Processing

• Staff Engineer

Queued

• Python Developer

Failed

• Frontend Engineer
```

When processing finishes successfully:

- The Job remains in the Jobs list.
- The Job status changes to **Processed**.
- The Queue entry is removed automatically.

The Job is **never moved** from the Jobs list into the Queue.

---

# Sections

The Processing Queue contains three sections.

```text
Processing

Queued

Failed
```

Completed Jobs are **not displayed** in the Processing Queue.

---

# Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Processing Queue                                   [Close]   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Processing (2)                                               │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Senior Backend Engineer                                  │ │
│ │ Extracting requirements...                               │ │
│ │ ███████████████─────────────── 62%                       │ │
│ │                                              [Cancel]    │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Queued (4)                                                   │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Python Developer                                         │ │
│ │ Waiting for an available worker                          │ │
│ │                                       [Start] [Remove]   │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Failed (1)                                                   │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Staff Engineer                                           │ │
│ │ Failed to fetch job page                                │ │
│ │                                      [Retry] [Remove]    │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

# Processing

Displays Jobs currently assigned to a worker.

Displayed information

- Job Title
- Current Step
- Progress
- Running Time (optional)

Available actions

- Cancel

Rules

- Cannot be reordered.
- Cannot be removed.
- Only one active processing entry exists per Job.

---

# Queued

Displays Jobs waiting for an available worker.

Displayed information

- Job Title
- Waiting Reason
- Queue Position (optional)

Possible waiting reasons

- Waiting for available worker
- Waiting after manual pause
- Scheduled retry

Available actions

- Start
- Remove

Rules

- Can be reordered.
- Can be removed from the queue.
- Removing from the queue does **not** delete the Job.

The Job remains in the Jobs list with status:

```text
Imported
```

---

# Failed

Displays Jobs that failed during processing.

Displayed information

- Job Title
- Failure Reason
- Last Attempt (optional)

Available actions

- Retry
- Remove

Rules

Retry creates a new Queue entry.

Remove only removes the Queue entry.

The Job remains in the Jobs list.

---

# Processing Completion

When processing finishes successfully:

1. Remove the Queue entry.
2. Update the Job status in the Jobs list if is in that list.

Example

Before

```text
Jobs List

Python Developer      Processing
```

```text
Processing Queue

Processing

• Python Developer
```

After

```text
Jobs List

Python Developer      Processed
```

```text
Processing Queue

(empty)
```

The Job is **never moved** between the Jobs list and the Processing Queue.

Only its processing status changes.

---

# Empty State

If there are no active Jobs:

```text
No Jobs are currently being processed.

Jobs added to the queue will appear here.
```

---

# Auto Refresh

The Processing Queue updates automatically when:

- A Job is queued.
- Processing starts.
- Progress changes.
- Processing completes.
- Processing fails.
- Processing is cancelled.
- A Job is retried.

Manual refresh should not be required.

---

# Actions

| Action | Description                                   |
| ------ | --------------------------------------------- |
| Cancel | Stop a running Job                            |
| Start  | Start processing a queued Job (when possible) |
| Retry  | Create a new Queue entry for a failed Job     |
| Remove | Remove the Job from the Processing Queue only |

---

# Queue Rules

- A Job can have at most one active Queue entry.
- Jobs are never removed from the Jobs list when queued.
- Processing Queue entries are temporary.
- Completed Jobs are automatically removed from the Queue.
- Failed Jobs remain in the Queue until removed or retried.
- Removing a Queue entry never deletes the Job.
- The Jobs list is the source of truth.
- The Processing Queue is a live execution view.

---

# States

- Empty
- Queued
- Processing
- Failed

---

# Related Documents

- `features/jobs/page.md`
- `features/jobs/add-job.md`
- `flows/jobs/create-and-queue-job.md`
- `flows/jobs/retry-job.md`
- `flows/jobs/cancel-job.md`
- `docs/job-state-machine.md`

```

```
