Implement cursor-based infinite scrolling for the new Jobs List.

## Goal

Replace the current paginated list with a modern infinite scrolling experience using the new Jobs API.

The backend already supports cursor pagination.

Do NOT implement classic page-based pagination.

---

## Requirements

### Data Fetching

- Use TanStack Query `useInfiniteQuery`.
- Consume the new cursor-based Jobs API.
- Request additional pages using the cursor returned by the backend.
- Preserve all previously loaded pages.
- Never replace already loaded rows while fetching.
- Cache pages correctly.

---

### Infinite Scrolling

- Automatically load the next page when the user scrolls near the bottom.
- Do not require a "Load More" button.
- Do not navigate between pages.

---

### Virtualization

Use TanStack Virtual.

Requirements:

- Virtualize only the visible rows.
- Keep scrolling smooth with thousands of jobs.
- Preserve scroll position while loading additional pages.
- Avoid unnecessary rerenders.

---

### Loading States

Initial loading:

- Display table skeleton rows.

Loading additional pages:

- Display a loading indicator at the bottom.

Example:

Loading more jobs...

---

### End of List

When there are no more pages:

Display:

You've reached the end

236 jobs loaded

---

### Header Information

Instead of page numbers, display:

Jobs (236)

Loaded 90 of 236 jobs

The loaded count should update after every fetched page.

The total count comes from the backend response.

---

### Empty State

If there are no jobs:

Display the existing empty state.

---

### Filtering

Infinite scrolling must continue working after:

- Search
- Sorting
- Filtering

Changing any filter should:

- Reset the cursor
- Clear previously loaded pages
- Load from the beginning

---

### UX

Never show:

- Page numbers
- Previous button
- Next button
- Page selector

This is NOT a paginated table.

It is an infinite scrolling list.

---

### Performance

The implementation must:

- Support tens of thousands of jobs.
- Avoid loading every job into memory.
- Keep rendering performant.
- Avoid duplicate requests.
- Cancel obsolete requests when filters change.

---

### Architecture

Follow the existing Feature-Sliced Design architecture.

Do not modify deprecated pages.

Implement this only for the new Jobs page.

Reuse existing shared UI components whenever possible.

Keep the implementation clean, modular, and production-ready.
