# Job Row

## Purpose

Defines the visual representation of a single Job inside the Jobs List.

The Jobs page is built from repeated Job Rows.

---

# Layout

Desktop

```
Title

Company

Location

Overall

Fit

Success

Processing

Updated

Actions
```

The layout is row-based.

Cards are intentionally not used.

---

# Displayed Information

Each row displays:

- Job Title
- Company
- Location
- Remote badge
- Visa badge
- Overall Score
- Fit Score
- Success Score
- Processing Status
- Last Updated
- Actions

---

# Score Presentation

Scores are displayed as compact badges.

Example

Overall

91

Fit

94

Success

88

---

# Processing Status

Displayed as a colored badge.

Possible values

- Queued
- Starting
- Running
- Completed
- Failed
- Cancelled

A job that has never been processed shows no processing badge (the list item
carries `latest_processing_execution = null`).

Running executions additionally display:

- spinner
- current progress

---

# Actions

The Actions column contains context-sensitive actions. All actions are
**icon-only buttons with tooltips**, keeping rows compact and scanable.

An **Edit** action is always available, allowing the user to update the Job's
core data (see `features/jobs/edit-job.md`).

A **Delete** action is always available, allowing the user to permanently remove
the Job and all its processing data (see `features/jobs/delete-job.md`).

No processing (never processed)

- Process (icon)
- Details (icon)
- Edit (icon)
- Delete (icon)

Running

- View Progress (icon)
- Edit (icon)
- Delete (icon)

Completed

- View Results (icon)
- Reprocess (icon)
- Edit (icon)
- Delete (icon)

Failed

- Retry (icon)
- Details (icon)
- Edit (icon)
- Delete (icon)

---

# Row Selection

Clicking anywhere on the row opens the Job Details Drawer.

Buttons do not trigger row selection.

---

# Hover Behavior

Hover highlights the entire row.

The current row becomes visually distinct.

---

# Live Updates

Rows update automatically using SSE.

The page must not reload.

Only the affected row should rerender.

When an execution reaches a terminal state, the list is refetched in the
background so the row shows the persisted pipeline output (extracted title,
final status) and stays correct across a reload.

---

# Responsive Behavior

Desktop

Full row layout.

Tablet

Some columns collapse.

Mobile

Rows become stacked.

Scores remain visible.

Actions stay icon-only (tooltips remain on tap).

---

# Accessibility

Rows support:

- keyboard navigation
- focus state
- screen readers

Buttons must remain individually accessible.

---

# Design Principles

The Job Row should prioritize:

- scanability
- information density
- fast comparison
- operational visibility

---

# Related Documents

- docs/ux/features/jobs/page.md
- docs/domain/jobs/job-list-item.md
- docs/api/jobs/list-jobs.md
