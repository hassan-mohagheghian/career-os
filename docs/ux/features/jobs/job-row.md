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

- Created
- Queued
- Starting
- Running
- Completed
- Failed
- Cancelled

Running executions additionally display:

- spinner
- current progress

---

# Actions

The Actions column contains context-sensitive actions.

Created

- Process V2
- Legacy Process
- Details

Running

- View Progress
- Details

Completed

- View Results
- Reprocess

Failed

- Retry
- Details

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

---

# Responsive Behavior

Desktop

Full row layout.

Tablet

Some columns collapse.

Mobile

Rows become stacked.

Scores remain visible.

Actions move into an overflow menu.

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
