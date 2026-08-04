# Favorite Job

## Purpose

The Favorite action lets the user bookmark a Job from the list so it can be
found again quickly through the Favorites filter.

Favoriting is a lightweight, user-managed flag. It is independent of the
analysis pipeline and does not affect scoring or recommendation.

---

# Related Page

Located in:

- `features/jobs/page.md`
- `features/jobs/job-row.md`

Triggered from the **Favorite** button on a **Job Row**.

Related:

- `api/jobs/list-jobs.md`

---

# Trigger

The **Favorite** button is a star icon in the row's dedicated first column.

- Empty star: not favorited.
- Filled (yellow) star: favorited.

The button is a separate interactive element. Clicking it never triggers row
selection (opening the Job Details drawer).

---

# User Goals

The user should be able to:

- Mark a promising job as a favorite
- See at a glance which jobs are favorited
- Remove a job from favorites
- Show only favorited jobs via the toolbar filter

---

# States

## Idle

The row shows an empty star (`☆`). Tooltip: *Add to favorites*.

## Favorited

The row shows a filled star (`★`). Tooltip: *Remove from favorites*.

## Toggling

The star updates **immediately** (optimistic update) before the request
finishes. `PUT /api/jobs/{job_id}/favorite` is sent to the server in the
background.

## Success

The star keeps its new state and the list query is invalidated so pagination
and totals stay in sync with the server.

## Error

The star is restored to its previous state (optimistic update rolled back) and
an error toast is shown.

---

# User Flow

```text
Open Jobs Page

↓

Click the star on a Job Row

↓

Star toggles immediately (optimistic update)

↓

PUT /api/jobs/{job_id}/favorite { favorite: bool }

↓

Success: query invalidated in the background
```

---

# Favorites Filter

The toolbar's star toggle restricts the list to favorited jobs.

```text
☆ All Jobs
★ Favorites only
```

When the filter is active, favoriting or unfavoriting a job refetches the list
so rows update immediately.

---

# Accessibility

- The icon button has an accessible label ("Add to favorites" /
  "Remove from favorites").
- The star exposes `aria-pressed` so screen readers announce the toggle state.

---

# Related Documents

- `features/jobs/page.md`
- `features/jobs/job-row.md`
- `api/jobs/list-jobs.md`
