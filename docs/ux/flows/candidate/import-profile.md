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
| System behavior | `POST /api/resumes` → stores next `original_N` row |
| UI state | Toast "Resume saved"; textarea cleared |

### Step 2 — Add LinkedIn

| | |
| --- | --- |
| User action | Paste LinkedIn text into the LinkedIn card, click **Save Profile** |
| System behavior | `POST /api/linkedin` → stores next `linkedin_N` row |
| UI state | Toast "LinkedIn profile saved"; textarea cleared |

### Step 3 — Analyze Profile

| | |
| --- | --- |
| User action | Click **✨ Analyze Profile** |
| System behavior | `POST /api/candidates/analyze` → creates + dispatches a `CANDIDATE_PROCESSING` execution (source preparation → extraction → merge → version) |
| UI state | Toast "Profile analysis queued"; Review tab activated |

```text
[✨ Analyze Profile]
        ↓ 202 { execution_id, status: queued }
   background workflow (SSE progress)
        ↓
   candidate profile v1 persisted
        ↓
   GET /profile, /sources, /versions refetch
```

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
- No sources at all → analysis still queues; sources-ready node degrades.

## Component Structure

```text
widgets/candidate-page
└── features/candidate-v2/components/ProfileImportPage
    ├── entities/candidate { api, hooks, types }
    ├── entities/resume { api.upload }
    └── entities/linkedin { api.upload }
```

## Data Dependencies

- `POST /api/candidates/analyze`, `GET /api/candidates/profile|sources|versions`.
- `POST /api/resumes`, `POST /api/linkedin` (existing jobs-context endpoints).
- SSE `/events/processing` for workflow progress.

# Related Documents

- `docs/ux/features/candidate/profile-import.md` (page spec)
- `implementation-history/103_candidate_profile_import.md` (phase prompt)
