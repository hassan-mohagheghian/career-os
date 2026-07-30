# Jobs Page

## Purpose

The Jobs page is the primary workspace for managing imported jobs.

It allows users to:

- Import new jobs
- Browse all imported jobs
- Search and filter jobs
- View job details
- Start processing
- Retry failed processing
- Monitor active processing
- Review completed jobs

A **Job** is the primary business entity.

The **Processing Queue** is a secondary workspace used only for monitoring background processing.

The queue never replaces the Jobs list.

---

# Design Goals

- Jobs are always the primary focus.
- Processing should never interrupt browsing.
- Queue monitoring should be available at any time.
- Opening the queue must not navigate away from the page.
- Users should always know what is currently processing.

---

# Page Structure

```
Jobs Page
│
├── Jobs Header
├── Toolbar
├── Job List
└── Processing Drawer (Hidden by default)
```

---

# Default Layout

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Jobs                                                                     [Queue] [+ Add Job] │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ [Search jobs...]                                                                             │
│ [Sorts]                                                                            [Filters] │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Senior Backend Engineer                                                           [More] │ │
│ │ Example Company                                                           Status: Queued │ │
│ └──────────────────────────────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Python Developer                                                                  [More] │ │
│ │ Company B                                                             Status: Processing │ │
│ └──────────────────────────────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Rust Backend Engineer                                                             [More] │ │
│ │ Company C                                                              Status: Processed │ │
│ └──────────────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# Processing Drawer

The Processing Drawer is opened from the **Queue** button.

It slides from the right without replacing the Jobs page.

```text
┌────────────────────────────────────────────────────┬─────────────────────────────────────────┐
│                                                    │ Processing Queue                        │
│ Job List                                           ├─────────────────────────────────────────┤
│                                                    │ Running                                 │
│ Job 1                                              │                                         │
│ Job 2                                              │ Job 8                     63%           │
│ Job 3                                              │ Job 12                    21%           │
│ Job 4                                              │                                         │
│                                                    ├─────────────────────────────────────────┤
│                                                    │ Waiting                                 │
│                                                    │                                         │
│                                                    │ Job 15                                  │
│                                                    │ Job 18                                  │
│                                                    │                                         │
│                                                    ├─────────────────────────────────────────┤
│                                                    │ Failed                                  │
│                                                    │                                         │
│                                                    │ Job 4                                   │
└────────────────────────────────────────────────────┴─────────────────────────────────────────┘
```

---

# Jobs Header

Responsibilities

- Display page title
- Open Processing Queue
- Add Job

Controls

| Control | Description             |
| ------- | ----------------------- |
| Queue   | Opens Processing Drawer |
| Add Job | Opens Import Job Drawer |

---

# Toolbar

Responsibilities

- Search jobs
- Filter jobs

Controls

| Control | Description                                |
| ------- | ------------------------------------------ |
| Search  | Search by title, company or keyword        |
| Filters | Filter by status, company, source and date |

---

# Job List

The Job List is the primary workspace.

Each item represents one Job.

Each card displays:

- Job title
- Company
- Status
- Quick actions

Selecting a card opens the Job Details Drawer.

---

# Job Card

Example

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Senior Backend Engineer                                                               [More] │
│ Example Company                                                           Status: Processing │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# Job Status

| Status     | Description                               |
| ---------- | ----------------------------------------- |
| Imported   | Job exists but processing has not started |
| Queued     | Waiting for an available worker           |
| Processing | Currently being processed                 |
| Processed  | Successfully completed                    |
| Failed     | Processing failed                         |

---

# Job Actions

## Imported

- Start Processing
- Delete

---

## Queued

- Cancel Queue
- Delete

---

## Processing

- View Progress
- Stop Processing

---

## Processed

- View Details
- Reprocess
- Delete

---

## Failed

- Retry
- View Error
- Delete

---

# Processing Queue

The Processing Drawer is divided into three sections.

```
Running

• Job 8
• Job 12

────────────────────────────

Waiting

• Job 15
• Job 18

────────────────────────────

Failed

• Job 4
```

---

# User Flow

## Import Job

```
Import Job

↓

Job Created

↓

Appears in Job List

↓

(Optional)

Start Processing
```

---

## Processing

```
Imported

↓

Queued

↓

Processing

├──→ Processed

└──→ Failed
```

---

## Retry

```
Failed

↓

Retry

↓

Queued

↓

Processing
```

---

# Responsive Behavior

## Desktop

- Full-width Job List
- Right-side Processing Drawer

## Tablet

- Narrower Drawer
- Responsive Job List

## Mobile

- Job List occupies full screen
- Processing Queue opens as a full-screen page

---

# Empty States

## No Jobs

- Empty illustration
- "No jobs have been imported yet."
- Add Job button

---

## Queue Empty

"No jobs are currently processing."

---

## Failed Empty

"No failed jobs."

---

# Icon Reference (Lucide)

| UI Element       | Lucide Icon       |
| ---------------- | ----------------- |
| Add Job          | Plus              |
| Queue            | LoaderCircle      |
| Search           | Search            |
| Filters          | SlidersHorizontal |
| More Menu        | Ellipsis          |
| Start Processing | Play              |
| Stop Processing  | Square            |
| Cancel Queue     | Pause             |
| Retry            | RotateCcw         |
| View Details     | Eye               |
| Delete           | Trash2            |
| Failed           | CircleX           |
| Processed        | CircleCheck       |
| Warning          | TriangleAlert     |

---

# Related Documents

- `docs/job-lifecycle.md`
- `docs/job-state-machine.md`
- `docs/workflow-progress.md`
- `docs/ux/design-system/`
- `docs/ux/wireframes/jobs/`
