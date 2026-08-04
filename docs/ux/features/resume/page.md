# Resume / Profile Page

The Resume page (`/resume`) manages the user's profile documents that drive job
scoring and resume/cover generation.

## Overview

The page has two tabs powered by `ResumeTab`:

- **Resumes** — master resumes stored as `original_N` (newest version first).
- **LinkedIn Profile** — pasted profiles stored as `linkedin_N` (newest version
  first).

Each tab is a list + preview layout. The active (latest) item is badged
**Active**. Deleting is per-item via the trash icon; the list auto-selects the
newest remaining item.

## Data source

- `GET /api/resumes` → all resume rows (frontend filters `original_*`).
- `GET /api/linkedin` → LinkedIn rows only, newest first.

## Upload Resume

- Trigger: **Upload Resume** button (header or empty state).
- Dialog: textarea pasting the resume text; personal info is masked on save.
- `POST /api/resumes` with `{ "raw_text": "…" }` → returns
  `{ "status": "saved", "version", "id" }`.
- Toast confirms `Resume v<N> saved`, then the list refreshes.

## Upload LinkedIn Profile

- Trigger: **Upload Profile** button (header or empty state).
- A yellow privacy notice explains that name, phone, email and LinkedIn/GitHub
  URLs are masked.
- `POST /api/linkedin` with `{ "raw_text": "…" }` → returns
  `{ "status": "saved", "version", "id" }`.

## Delete

- Trash icon on each row calls `DELETE /api/resumes/{id}` or
  `DELETE /api/linkedin/{id}` (id, not version). A 404 on an unknown id shows
  the delete toast and refreshes.

## States

- **Empty**: card with icon, helper copy and an upload button.
- **Loading/saving**: buttons disable and show "Saving…".
- **Preview**: clicking a row shows the rendered `content` HTML in the right
  pane; **Close** collapses it.
