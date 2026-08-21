# Application Notes

> Feature doc for the **Notes** section of the Job Application Workspace
> (`/jobs/{job_id}/application`). See `workspace.md` for the page overview.

# Purpose

Let the user record their application activities **in their own words** —
calls with recruiters, emails sent, interview impressions, decisions — as
simple free-text notes, each stamped with its creation time. Notes make the
user's activity around an application traceable over time.

# User Goals

- Add a note to an application (any free text, no structure required)
- See all notes for the application, **newest first**, with creation time
- Delete a note that is no longer needed

---

# Layout & States

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ NOTES                                                                    │
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ What happened? (call, email, interview impression, decision…)        │ │
│ │                                                                      │ │
│ │                                                          [Add Note]  │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  Recruiter call — positive, next step: tech interview                    │
│  Aug 21, 2026 14:02                                               [🗑]   │
│ ──────────────────────────────────────────────────────────────────────── │
│  Sent tailored resume via LinkedIn                                       │
│  Aug 20, 2026 09:47                                               [🗑]   │
│ ──────────────────────────────────────────────────────────────────────── │
└──────────────────────────────────────────────────────────────────────────┘

States:
  empty input + not pending   → [Add Note] disabled
  pending                     → [Add Note] shows spinner, disabled
  no notes yet                → "No notes yet. Use notes to track your
                                 application activity in your own words."
  delete                      → per-note trash button (no confirm)
```

The section renders only when an application exists (same as Tracker /
Roadmap / Documents), placed after Documents.

---

# Flow

```mermaid
flowchart TD
    A[User types a note in the textarea] --> B{Content non-empty?}
    B -- no --> C[Add Note disabled]
    B -- yes --> D[Click Add Note / Enter]
    D --> E[POST /api/applications/{id}/notes]
    E --> F[Backend validates application exists<br/>stores content + created_at<br/>emits application.note.added]
    F --> G[Detail refetched - list shows newest first]
    H[User clicks trash on a note] --> I[DELETE /api/applications/notes/{note_id}]
    I --> J[Row hard-deleted<br/>emits application.note.deleted]
    J --> G
```

---

# Behaviors

| Action | Behavior |
| ------ | -------- |
| Add Note | `POST /api/applications/{id}/notes` with `{ "content": "…" }` → 201 + note. Content is trimmed; empty/whitespace content is rejected (422). The application detail is invalidated and refetched, so the new note appears at the top (newest first). The textarea clears after a successful add. |
| Enter key | Submits the note (same as clicking Add Note) while the textarea is focused. |
| Delete | `DELETE /api/applications/notes/{note_id}` → 204, hard delete, detail refetch. |
| Ordering | Notes are listed newest first (`created_at DESC`) — rule 7. |
| Timestamps | Each note shows its creation time (`DateTime` component). Notes are immutable — there is no edit action. |

# API

| Endpoint | Purpose |
| -------- | ------- |
| `POST /api/applications/{application_id}/notes` | Add a note (`content`). Returns the stored note. |
| `DELETE /api/applications/notes/{note_id}` | Hard-delete a note. |
| `GET /api/applications/by-job/{job_id}` / `GET /api/applications/{id}` | Detail responses embed `notes[]` (newest first). |

# Domain Events

- `application.note.added` (`ApplicationNoteAdded`) — fired by `NoteService.add`.
- `application.note.deleted` (`ApplicationNoteDeleted`) — fired by `NoteService.delete`.

Documented in `docs/domain/applications/events.md`; pub/sub deferred (rule 16).

---

# Related Documents

- `features/applications/workspace.md`
- `docs/domain/applications/events.md`
