# Candidate Profile Import Page

## Purpose

The Candidate Profile Import page is the first page of the Candidate module.
It lets the user import their professional information (resume, LinkedIn, and
an optional GitHub placeholder), run AI profile analysis, and review the
resulting canonical candidate profile (skills, experience, projects, sources,
summary).

Actions available on this page:

- Upload / replace the resume (paste text).
- Upload / replace the LinkedIn profile (paste text).
- See the last-updated time of each saved source and view its stored content
  (PII-masked) in a dialog.
- Enter a GitHub username (optional, placeholder for a future phase).
- Run **Analyze Profile** — queues candidate processing via
  `POST /api/candidates/analyze`.
- Open the **Processing** queue drawer (same drawer as Jobs / Companies,
  filtered to `target_type="candidate"`) to watch the analysis workflow steps
  and progress.
- Review the extracted profile, connected sources and version history.
- Confirm / retry the analysis (post-hoc confirm model: extraction already
  persists; Confirm acknowledges the result).

## Design Principles

- Two-tab layout: **Sources** (input) and **Review** (output).
- Uploads use the candidate source endpoint (`POST /api/candidates/sources`),
  storing raw text as the next source version (PII masked, status `pending`).
- Every saved source shows a relative **last-updated** timestamp (full local
  datetime on hover) and a **View** action that opens a read-only dialog with the
  stored (PII-masked) content — giving immediate feedback that the save succeeded.
- GitHub is clearly marked as a placeholder.
- Profile analysis is a background workflow; the UI queues it and lets the user
  switch to Review to see the latest persisted profile, or open the Processing
  drawer to watch the `CANDIDATE_PROCESSING` workflow progress live via SSE
  (same component as Jobs / Companies, filtered to `target_type="candidate"`).

# High-Level Layout

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Candidate Profile                                        [nav: Candidate]│
├──────────────────────────────────────────────────────────────────────────┤
│ [Sources] [Review]                                                       │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────┐  ┌──────────────────────────┐               │
│ │ RESUME (card)            │  │ LINKEDIN (card)          │               │
│ │  ✎ paste textarea        │  │  ✎ paste textarea        │              │
│ │  [Save Resume]           │  │  [Save Profile]          │               │
│ │  Last updated 5m ago · v2│  │  Last updated 3d ago · v1│               │
│ │  [👁 View]               │  │  [👁 View]               │                │
│ └──────────────────────────┘  └──────────────────────────┘               │
│ ┌────────────────────────────────────────────────────────────────────┐   │
│ │ GITHUB (optional, card) — username input  [placeholder]            │   │
│ └────────────────────────────────────────────────────────────────────┘  │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ ANALYZE PROFILE (card)                                             │  │
│ │  [✨ Analyze Profile]  [☑ Processing]   (queues candidate run)      │  │
│ └────────────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────┤
│  [Review tab]                                                           │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ PROFILE SUMMARY (card)  name · title · version · location           │  │
│ │ headline / summary                                                  │  │
│ │ [2 skills] [1 experience] [1 project] [1 education] [1 language]    │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────┐  ┌──────────────────────────┐              │
│ │ CONNECTED SOURCES        │  │ VERSION HISTORY          │              │
│ │  resume v2 [pending] 5m  │  │  v2 "added linkedin"     │              │
│ │   [👁 View]              │  │  v1 "initial import"     │              │
│ │  linkedin v1 [processed] │  └──────────────────────────┘              │
│ │   3d [👁 View]           │                                           │
│ └──────────────────────────┘                                           │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ SKILLS  [Python L4 96%] [PostgreSQL L4 90%] ...                    │  │
│ ├────────────────────────────────────────────────────────────────────┤  │
│ │ EXPERIENCE  role · company · dates · summary                       │  │
│ ├────────────────────────────────────────────────────────────────────┤  │
│ │ PROJECTS  name · description · url                                 │  │
│ └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

# Component Hierarchy

```text
ProfileImportPage
├── PageHeader
├── Tabs (Sources | Review)
├── Sources tab
│   ├── SourceCard (Resume)      → Textarea + [Save Resume] + last-updated + [👁 View]
│   ├── SourceCard (LinkedIn)    → Textarea + [Save Profile] + last-updated + [👁 View]
│   ├── GitHub card              → Input (placeholder)
│   └── Analyze card             → [✨ Analyze Profile] + [☑ Processing]
├── Review tab
│   ├── ProfileReview            → summary + badge counts
│   ├── SourcesCard              → source list + last-updated + [👁 View] per row
│   ├── VersionsCard             → version history
│   ├── SkillCloud               → skill badges
│   ├── ExperienceList
│   └── ProjectList
├── SourceContentDialog          → read-only dialog with stored source text
└── ProcessingDrawer             → queue drawer filtered to target_type="candidate"
```

# Component/Data Flow

```mermaid
flowchart LR
    subgraph Sources
        R[Resume paste] --> RS[POST /api/candidates/sources]
        L[LinkedIn paste] --> LS[POST /api/candidates/sources]
    end
    subgraph Analyze
        A[Analyze Profile] --> AP[POST /api/candidates/analyze]
        AP --> EX[Execution created + dispatched]
        EX -. SSE /events/processing .-> W[ProcessingDrawer progress]
    end
    subgraph Review
        P[GET /api/candidates/profile]
        S[GET /api/candidates/sources]
        V[GET /api/candidates/versions]
    end
    EX --> P
    EX --> S
    EX --> V
    R --> P
    L --> P
```

# View Source Content Flow

```mermaid
sequenceDiagram
    actor U as User
    participant UI as SourcesCard / SourceCard
    participant D as SourceContentDialog
    U->>UI: click 👁 View
    UI->>D: open(source dict from cached GET /sources)
    D-->>UI: read-only <pre> of masked raw_text
    U->>D: close
    D-->>UI: onOpenChange(false) → clear viewSource
```

# State Diagram

```mermaid
stateDiagram-v2
    [*] --> SourcesTab
    SourcesTab --> Analyze: analyze clicked
    Analyze --> Queued: 202 {execution_id}
    Queued --> Review: switch to Review tab
    Review --> ProfileLoaded: GET profile ok
    Review --> ProfileMissing: 404 (no profile)
    ProfileLoaded --> Analyze: re-run analysis
    ProfileMissing --> Analyze: run analysis first
```

# Behaviors

| Element         | Behavior                                                                                                                                                                           |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sources tab     | Default tab. Resume + LinkedIn paste cards, GitHub placeholder, Analyze card.                                                                                                      |
| Save Resume     | `POST /api/candidates/sources` with `{ source_type: "resume", raw_text }`; toast on success; clears textarea; sources query invalidated so last-updated + View update immediately. |
| Save Profile    | `POST /api/candidates/sources` with `{ source_type: "linkedin", raw_text }`; toast on success; clears textarea; sources query invalidated.                                         |
| View content    | [👁 View] on a SourceCard or a Connected Sources row opens `SourceContentDialog` showing the stored (PII-masked) raw text in a scrollable read-only block.                          |
| Last updated    | Relative timestamp (`updated_at` or `created_at`) on each SourceCard footer and each Connected Sources row; hover shows the full local datetime.                                   |
| GitHub input    | Stored locally only; marked "not yet available" (adapter is a stub).                                                                                                               |
| Analyze Profile | `POST /api/candidates/analyze`; returns `{ execution_id, status }`; toast "queued"; switches to Review. |
| Processing | [☑ Processing] opens the shared `ProcessingDrawer` filtered to `target_type="candidate"` — running / waiting / failed candidate executions with workflow step progress (SSE live updates). |
| Review tab      | Fetches `/api/candidates/profile`, `/sources`, `/versions` on mount and after analysis via React Query invalidation.                                                               |
| Confirm / retry | Post-hoc confirm: no separate confirm step; re-running analysis is the retry path.                                                                                                 |

# Empty States

```text
┌──────────────────────────────────────┐
│ No profile yet.                      │
│ Add your resume / LinkedIn sources   │
│ and run [✨ Analyze Profile].        │
└──────────────────────────────────────┘
```

- Connected Sources: "No sources imported yet."
- Version History: "No profile versions yet."
- Skills / Experience / Projects sections are hidden when empty.

# Loading States

- Review tab: "Loading profile..." while `GET /profile` is in flight.
- Analyze button: label becomes "Queuing analysis..." and is disabled while the
  mutation is pending.

# Error States

- Profile fetch failure: "Could not load the candidate profile." + [Retry].
- Analyze failure: toast "Failed to start profile analysis"; inline error text
  under the Analyze button.

# Responsive Behavior

- Two source cards stack into a single column on small screens (`lg:grid-cols-2`
  → one column below `lg`).
- Source/version cards sit side by side on wide screens, stacked on mobile.

# Navigation

- Nav item **Candidate** (`/candidate`) between Companies and Skills.
- No cross-page navigation yet; dashboard (110 Phase 2) will become the landing
  page in a later phase.

# Related Documents

- `docs/ux/flows/candidate/import-profile.md` (user journey)
- `DESIGN.md` (nav tree + wireframes)
