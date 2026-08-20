# Drag-and-Drop Link Import Flow

## Purpose

This flow describes how the user adds a new Job by **dragging a link from
another browser tab** into the app and dropping it onto the Jobs page.

The drop only **opens the Add Job drawer pre-filled** with the dropped URL. It
never auto-creates or auto-queues a job — the user then chooses **Add** (save
only) or **Add & Queue** (save + process) as usual.

---

## Trigger

The user drags a link from another tab (a job posting) into the app and drops
it onto either:

- the **Add Job** button, or
- **anywhere on the Jobs page**.

If the user is not already on the Jobs page, they first navigate there via the
Jobs menu item (the drop surface only exists on the Jobs page).

---

## Preconditions

- The user is on the **Jobs page** (drop target present).
- The dragged payload contains an `http(s)` URL (delivered by the browser via
  `text/uri-list` or `text/plain`).

---

## Drop Targets

```text
┌────────────────────────────────────────────────────────────────┐
│ Jobs (10)                                                       │
│                                                    ┌─────────┐ │
│   [Queue]                                [Add Job] │ <- drop │ │
│                                                    └─────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  …dragging a URL anywhere here shows a                   │  │
│  │     "Drop to add job" overlay                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
        drop target 1 = Add Job button (highlights emerald on hover)
        drop target 2 = entire Jobs page (full-page drop surface)
```

---

## Flow

```text
On Jobs page, drag a link from another tab

        │

        ▼

Hover over Add Job button OR any point on the page

        │

        ├──────────────────────────────────────────── Drop over button
        │           button highlights (emerald ring)
        │
        ▼                                       Drop anywhere on page
"Drop to add job" indicator overlay            full-page drop surface
        │
        ▼
Drop the link

        │
        ▼
Extract http(s) URL from dataTransfer          (uri-list → text/plain)

        │

        ├────────────────────────── not a URL
        │        ignored (no action)
        │
        ▼
Valid URL

        │
        ▼
Open Add Job drawer, pre-filled with the URL

        │
        ▼
User presses "Add"  or  "Add & Queue"
        │               │
        ▼               ▼
  Save only         Save + process        (existing create-job / queue-job flow)
```

---

## Behavior Details

- **Pre-fill only.** Dropping never creates or queues a job. The Add Job drawer
  opens with the Job Post URL field filled in from the dropped URL; the user
  decides to Add or Add & Queue.
- **Dropping on the Add Job button** also opens the same pre-filled drawer. The
  button stops event propagation so the page-wide surface does not also fire.
- **Non-URL drops** (files, plain text without a URL) are silently ignored; no
  drawer opens, no error shown.
- **No backend change.** The drawer's existing `POST /api/jobs` with its `queue`
  flag already covers both Add and Add & Queue.

---

## States

| State                        | Description                                              |
| ---------------------------- | -------------------------------------------------------- |
| Dragging over button         | Button shows emerald ring; drawer not yet opened.        |
| Dragging over page           | "Drop to add job" overlay shown (non-interactive).       |
| Dropped URL                  | Add Job drawer opens with URL pre-filled.                |
| Dropped non-URL              | Nothing happens.                                         |
| Drawer Add                   | Job saved (Imported), list refreshed (existing flow).    |
| Drawer Add & Queue           | Job saved and queued, queue drawer opens (existing flow).|

---

## Related Documents

- `features/jobs/add-job.md`
- `flows/jobs/create-job.md`
- `flows/jobs/queue-job.md`
- `features/jobs/page.md`