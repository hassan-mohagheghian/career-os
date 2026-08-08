# Import Candidate Profile — Flow

## Purpose

The user journey for building a canonical candidate profile for the first time:
import sources, run AI analysis, and review the extracted profile. This is the
first end-to-end flow of the Candidate module (110 Phase 1).

## Overview

```text
Resume paste
     ↓
LinkedIn paste
     ↓
GitHub username (optional, placeholder)
     ↓
Analyze Profile
     ↓
Candidate processing execution (queued → running)
     ↓
Merge into canonical profile + new version
     ↓
Review profile (skills / experience / projects / sources / versions)
```

## Entry Points

- Header nav **Candidate** → `/candidate` (always visible, no gate).

## User Action / System Behavior / UI State

### Step 1 — Add resume

| | |
| --- | --- |
| User action | Paste resume text into the Resume card, click **Save Resume** |
| System behavior | `POST /api/candidates/sources` with `{ source_type: "resume", raw_text }` → stores the next resume source version (`pending`); sources query invalidated |
| UI state | Toast "Resume saved"; textarea cleared; Resume card footer updates to the new version + relative last-updated time with a [👁 View] action |

### Step 2 — Add LinkedIn

| | |
| --- | --- |
| User action | Paste LinkedIn text into the LinkedIn card, click **Save Profile** |
| System behavior | `POST /api/candidates/sources` with `{ source_type: "linkedin", raw_text }` → stores the next LinkedIn source version (`pending`); sources query invalidated |
| UI state | Toast "LinkedIn profile saved"; textarea cleared; LinkedIn card footer updates to the new version + relative last-updated time with a [👁 View] action |

### Step 2b — View a saved source

| | |
| --- | --- |
| User action | Click **👁 View** on a SourceCard footer or a Connected Sources row |
| System behavior | No network call — the source dict (returned by `GET /api/candidates/sources`) already carries the stored (PII-masked) `raw_text` |
| UI state | `SourceContentDialog` opens with the source title (`resume v2`) and a scrollable read-only pre block of the stored content |

### Step 3 — Analyze Profile

| | |
| --- | --- |
| User action | Click **✨ Analyze Profile** |
| System behavior | `POST /api/candidates/analyze`. When the profile has a source still to process (`pending` / `failed`): creates + dispatches a `CANDIDATE_PROCESSING` execution (source preparation → extraction → merge → version). When every source is already `processed` (or none exist): returns `200 { status: "noop", reason: "no_new_sources" }` and queues nothing |
| UI state | Queued path: toast "Profile analysis queued"; Review tab activated. Noop path: info toast "No new resume/LinkedIn version to process — save a new version first"; stays on Sources |

```text
[✨ Analyze Profile]
        ↓ POST /api/candidates/analyze
   ┌──────────────┴───────────────┐
   │ new pending source?          │
   ├── yes ── 202 {execution_id, status: queued}
   │             ↓ background workflow (SSE progress)
   │             ↓ candidate profile v{N} persisted
   │             ↓ GET /profile, /sources, /versions refetch
   └── no ── 200 {status: noop, reason: no_new_sources}
                 ↓ info toast (no run queued)
```

### Step 3b — Watch analysis progress

| | |
| --- | --- |
| User action | Click **☑ Processing** in the Analyze card |
| System behavior | `GET /api/processing/queue` returns candidate executions (`target_type="candidate"`); workflow step details via `GET /api/processing/{execution_id}`; live SSE step events merge into the workflow |
| UI state | Shared `ProcessingDrawer` (same as Jobs/Companies) shows running / waiting / failed candidate runs with step checklist + progress bars; "No candidate analysis in this state." when the queue is empty |

### Step 4 — Review

| | |
| --- | --- |
| User action | Inspect Profile Summary, Skills, Experience, Projects, Sources, Version History |
| System behavior | Three React Query GETs; refreshed after analysis |
| UI state | Post-hoc confirm: profile already persisted; re-running analysis is the retry/update path |

## Loading / Failed / Empty States

- **Loading**: Review shows "Loading profile...".
- **Failed**: analyze → toast error + inline message; profile fetch → "Could not
  load the candidate profile." + Retry.
- **Empty**: "No profile yet" card when `GET /profile` returns 404.

## Edge Cases

- Resume/LinkedIn empty text → Save buttons disabled.
- Re-importing the same source version → workflow skips it (`already_processed`).
- No unprocessed sources at all (all `processed`, or none) → `POST /analyze`
  returns `200 status=noop`, no execution queued; info toast explains that a new
  resume/LinkedIn version must be saved first.
- Source without content → View dialog shows "No content saved."

## Component Structure

```text
widgets/candidate-page
└── features/candidate-v2/components/ProfileImportPage
    ├── entities/candidate { api, hooks, types }
```

## Data Dependencies

- `POST /api/candidates/sources` (upload resume / LinkedIn source text).
- `POST /api/candidates/analyze`, `GET /api/candidates/profile|sources|versions`.
- SSE `/events/processing` for workflow progress.

# Related Documents

- `docs/ux/features/candidate/profile-import.md` (page spec)
- `implementation-history/103_candidate_profile_import.md` (phase prompt)
