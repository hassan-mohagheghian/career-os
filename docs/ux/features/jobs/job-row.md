# Job Row

## Purpose

Defines the visual representation of a single Job inside the Jobs List.

The Jobs page is built from repeated Job Rows.

---

# Layout

Desktop

```
Favorite

Title

Company

Location

Overall

Fit

Success

Recommendation

Processing

Updated

Actions
```

The layout is row-based.

Cards are intentionally not used.

---

# Displayed Information

Each row displays:

- Favorite
- Job Title
- Company
- Location
- Remote badge
- Visa badge
- Overall Score
- Fit Score
- Success Score
- Recommendation
- Processing Status
- Last Updated
- Actions

---

# Favorite

A leading star button toggling the job's favorite flag (see
`features/jobs/favorite-job.md`).

- Empty star: not favorited.
- Filled star: favorited.

The toggle is optimistic — the star updates immediately and is rolled back on
failure. The button is a separate interactive element and does not trigger row
selection.

---

# Recommendation

A compact badge showing the analysis recommendation derived from the Overall
Score:

| Recommendation | Meaning            | Color   |
| -------------- | ------------------ | ------- |
| Apply          | Overall ≥ 80       | Emerald |
| Consider       | Overall ≥ 60       | Amber   |
| Skip           | Otherwise          | Gray    |

Jobs without a completed analysis show an em dash (`—`) instead of a badge.

The badge is display-only: it is not clickable and does not open the Job
Details drawer.

# Score Presentation

Scores are displayed as compact badges, led by the overall grade badge
(derived from the overall score via the shared grade helper, `A++` … `D`).

Example

Grade

A+

Overall

91

Fit

94

Success

88

```text
[A+]  O 91   F 94   S 88
```

Null scores show `—`; a missing overall score shows `—` for the grade instead
of `P`.

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
