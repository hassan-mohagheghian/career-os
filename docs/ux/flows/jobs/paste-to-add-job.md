# Paste-to-Add Job Flow (Ctrl/Cmd+V)

## Purpose

This flow describes how the user adds a new Job by **copying a job-posting
link anywhere** (another tab, an email, a chat) and pressing **Ctrl+V /
Cmd+V on the Jobs page**.

The paste only **opens the Add Job drawer pre-filled** with the pasted URL.
It never auto-creates or auto-queues a job — the user then chooses **Add**
(save only) or **Add & Queue** (save + process) as usual.

---

## Trigger

The user presses **Ctrl+V** (Windows/Linux) or **Cmd+V** (macOS) while the
Jobs page is open and no editable element has focus.

If the user is not already on the Jobs page, they first navigate there via
the Jobs menu item (the paste shortcut only exists on the Jobs page).

---

## Preconditions

- The user is on the **Jobs page** (paste listener mounted).
- The focus is **not** inside an input, textarea, select or content-editable
  element (there, native paste applies).
- The clipboard contains `http(s)` text (validated with the shared URL regex).

---

## Wireframe

```text
┌────────────────────────────────────────────────────────────────┐
│ Jobs (10)                                    [Add Job]         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Copy a job link anywhere, come back, press Ctrl+V       │  │
│  │     ──► Add Job drawer opens, Job Post URL pre-filled    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘

        focus in a search/input box  ──► normal paste into the field
        clipboard without a URL      ──► nothing happens
```

---

## Flow

```text
On Jobs page, press Ctrl/Cmd+V with a copied link

        │

        ▼

Focus inside an input / textarea / select / contentEditable?

        │

        ├────────────────────────────── yes ──► native paste (no hijack)
        │
        ▼ no

Read text/plain from the clipboard event

        │

        ├────────────────────────── not an http(s) URL
        │        ignored silently (no action, native behavior kept)
        │
        ▼ Valid URL

preventDefault + open Add Job drawer pre-filled with the URL

        │

        ▼

User presses "Add"  or  "Add & Queue"
        │               │
        ▼               ▼
  Save only         Save + process        (existing create-job / queue-job flow)
```

---

## Mermaid Diagram

```mermaid
flowchart TD
    A[User copies job link anywhere] --> B[On Jobs page, presses Ctrl/Cmd+V]
    B --> C{Focus in editable element?}
    C -- yes --> D[native paste into the field]
    C -- no --> E[Read text/plain from clipboard event]
    E --> F{Is http(s) URL?}
    F -- no --> G[Ignored silently]
    F -- yes --> H[preventDefault<br/>Open Add Job drawer, Job Post URL pre-filled]
    D --> I([done])
    G --> I
    H --> J{User chooses}
    J -- Add --> K[Save only - existing create-job flow]
    J -- Add & Queue --> L[Save + queue - existing queue-job flow]
```

---

## Behavior Details

- **Pre-fill only.** Pasting never creates or queues a job. The Add Job
  drawer opens with the Job Post URL field filled in from the pasted URL; the
  user decides to Add or Add & Queue.
- **No permission prompt.** Unlike the button/N-key entry points (which use
  `navigator.clipboard.readText()`), the payload comes straight from the
  `paste` event's `clipboardData` — no `clipboard-read` permission needed.
- **Native paste preserved.** When the focus is in any editable element
  (search box, drawer fields), the event is not intercepted — normal pasting
  works exactly as before.
- **Pasting while the drawer is already open** replaces the Job Post URL
  value (same reactive pre-fill path as drag-and-drop).
- **Non-URL clipboard content** (plain words, files) is silently ignored; no
  drawer opens, no error shown.
- **Jobs-page scope.** Like the `N` shortcut, the listener is mounted by the
  Jobs page widget only.
- **No backend change.** The drawer's existing `POST /api/jobs` with its
  `queue` flag already covers both Add and Add & Queue.

---

## States

| State                        | Description                                              |
| ---------------------------- | -------------------------------------------------------- |
| Ctrl/Cmd+V with URL          | Add Job drawer opens with URL pre-filled.                |
| Focus in editable element    | Native paste into that field; drawer untouched.          |
| Clipboard without URL        | Nothing happens (default paste behavior kept).           |
| Drawer Add                   | Job saved (Imported), list refreshed (existing flow).    |
| Drawer Add & Queue           | Job saved and queued, queue drawer opens (existing flow).|

---

## Related Documents

- `features/jobs/add-job.md`
- `flows/jobs/drag-drop-job.md`
- `flows/jobs/create-job.md`
- `flows/jobs/queue-job.md`
- `features/jobs/page.md`
