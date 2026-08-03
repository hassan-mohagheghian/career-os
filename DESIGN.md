# Product & UX Design

## Design Language

Job Search Intelligence is a **dense, data-focused dashboard** built for software engineers comparing many job opportunities at once.

- **UI library**: shadcn/ui primitives (Radix UI + Tailwind CSS)
- **Icons**: Lucide
- **Density tokens**: custom Tailwind font sizes `text-3xs` (6px) and `text-2xs` (8px) for compact tables and cards
- **Status colors**: Ready (gray), Queued (blue), Running (cyan), Completed (green), Failed (red), Cancelled (orange)
- **Score grades**: A++ / A+ (green), A (lime), B (blue), C (orange), D (red)

The interface follows WCAG AA: keyboard navigation, focus management, screen-reader labels, and ARIA progress indicators.

---

## Navigation Structure

```
JOBS
  ├── Jobs           Job list (infinite scroll) + Processing Queue drawer
  └── Companies      Company intelligence + processing queue

GROWTH PATH
  └── Skills         Skill management, roadmaps, progress

INSIGHTS
  ├── Overview       Career health score, next actions
  ├── Opportunities  Job funnel, best jobs
  ├── Companies      Company scoring, top targets
  ├── Market         Countries, cities, remote opportunities
  ├── Networking     Connection strategy, LinkedIn targets
  └── Skills         Skills analysis

SETTINGS
  ├── Resume         Resume / cover letter generation
  └── Rules          Scoring rules configuration
```

---

## Design System

### Drawer

The Drawer is the primary secondary workspace. It opens without leaving the current page.

| Variant | Width | Typical Usage        |
| ------- | ----: | -------------------- |
| xs      | 320px | Confirmations        |
| sm      | 420px | Filters, simple forms |
| md      | 560px | Processing Queue     |
| lg      | 720px | Company Details      |
| xl      | 960px | Job Details          |
| full    |  100% | Mobile / full screen |

Placement is right by default; all variants become full-screen on mobile.

---

## Wireframes

### Jobs Page

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Jobs                                          Queue (2 Running · 4 Waiting)  + Import │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Search .......................................................................       │
│ Sort ▼                  Filters ▼                                        Refresh     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ # │ Job                  │ Company    │ Location │ Overall │ Fit │ Proc.  │ Updated │
│─────────────────────────────────────────────────────────────────────────────────────│
│ 1 │ Senior Backend Eng.  │ GetYourGuid│ Berlin   │ A++  94  │ 95  │ Ready  │ 2m      │
│ 2 │ Backend Engineer     │ Karla      │ Berlin   │ A+  90   │ 90  │ Running│ now     │
│ 3 │ Python Developer     │ Flexa      │ Remote   │ A   86   │ 86  │ Failed │ 5m      │
│                                                                                     │
│                                       Loading more jobs...                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Processing Queue Drawer

```text
┌─────────────────────────────────────────────┐
│ Processing Queue                      Close │
├─────────────────────────────────────────────┤
│ Processing (2)                              │
│ ┌─────────────────────────────────────────┐ │
│ │ Senior Backend Engineer                 │ │
│ │ Fetching Sources                        │ │
│ │ ██████████████░░░░ 60%                  │ │
│ │                             Details    │ │
│ └─────────────────────────────────────────┘ │
│ Queued (3)                                  │
│ ┌─────────────────────────────────────────┐ │
│ │ Python Developer                        │ │
│ │ Position #1                             │ │
│ │                        Start    Remove  │ │
│ └─────────────────────────────────────────┘ │
│ Failed (1)                                  │
│ ┌─────────────────────────────────────────┐ │
│ │ Frontend Engineer                       │ │
│ │ Failed to fetch source                  │ │
│ │                         Retry   Remove  │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Add Job Drawer

```text
┌─────────────────────────────────────────────┐
│ Add Job                              [Close]│
├─────────────────────────────────────────────┤
│ Job Post URL *                              │
│ ┌─────────────────────────────────────────┐ │
│ │ https://...                             │ │
│ └─────────────────────────────────────────┘ │
│ Job Title (Optional)                        │
│ ┌─────────────────────────────────────────┐ │
│ │ Senior Backend Engineer                 │ │
│ └─────────────────────────────────────────┘ │
│ Additional Links                     [+Add] │
│ No additional links                         │
│ Notes                                [+Add] │
│ No notes                                    │
├─────────────────────────────────────────────┤
│                     [Cancel] [Create] [Queue]│
└─────────────────────────────────────────────┘
```

### Edit Job Drawer

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Edit Job                                                      [Close]│
├──────────────────────────────────────────────────────────────────────┤
│ Title (Optional)                                                     │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Staff Software Engineer                                          │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ Role (Optional)                                                     │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │                                                                  │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ Company (Optional)                                                  │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Acme GmbH                                                        │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ Location (Optional)                                                 │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Berlin                                                           │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ Job Post URL *                                                     │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ https://...                                                      │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ Work Type        Employment Type                                   │
│ ┌─────────────┐  ┌──────────────┐                                  │ │
│ │ On-site    ▾│  │ Full-time   ▾│                                  │ │
│ └─────────────┘  └──────────────┘                                  │ │
│ Visa (Optional)     Salary (Optional)                              │
│ ┌─────────────┐  ┌──────────────┐                                  │ │
│ │ Strong      │  │ €90k - €110k  │                                  │ │
│ └─────────────┘  └──────────────┘                                  │ │
│ Description                                                        │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Work alongside a cross-functional team...                       │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ Notes (editable, add/remove)                                       │
│ Additional Links (editable, add/remove)                            │
├──────────────────────────────────────────────────────────────────────┤
│                              [Cancel]                        [Save]  │
└──────────────────────────────────────────────────────────────────────┘
```

### Job Details Drawer

Shows the full record for a row, including the AI Analysis block produced by
the Job Analysis phase. The Analysis section renders only once the analysis
phase completes (data is refetched on the `execution.completed` SSE event).

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ Job Details                                                             [Close]│
├───────────────────────────────────────────────────────────────────────────────┤
│ Senior Backend Engineer                                                      │
│ Acme Inc  ·  Berlin, Germany  ·  Hybrid  ·  Full-time                        │
│ Open job posting ↗                                                           │
│                                                                              │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐                                    │
│ │ Overall   │ │ Fit       │ │ Success   │                                    │
│ │ 79        │ │ 85        │ │ 70        │                                    │
│ └───────────┘ └───────────┘ └───────────┘                                    │
│                                                                              │
│ ┌─ AI Analysis ────────────────────────────────────────────────────────────┐ │
│ │ [consider]           2026-08-03 12:00                                    │ │
│ │ Great role overall. It matches the senior backend profile...             │ │
│ │ • Mention Kafka coursework                                               │ │
│ │ • Ask about salary band                                                  │ │
│ ├─ Scores Explanation ────────────────────────────────────────────────────┤ │
│ │ WHY IT FITS                                                              │ │
│ │ • Python backend experience                                              │ │
│ │ CHANCE OF SUCCESS                                                        │ │
│ │ • Senior level · Berlin                                                  │ │
│ │ CONCERNS                                                                 │ │
│ │ • No Kafka experience (red)                                              │ │
│ ├─ Summary ────────────────────────────────────────────────────────────────┤ │
│ │ Backend role at Acme.                                                    │ │
│ │ Resume fit: Strong fit.  Note: Apply early.                              │ │
│ ├─ Tagged Skills ─────────────────────────────────────────────────────────┤ │
│ │ [Python · L4 · Language] [Postgres · L4 · Data]                          │ │
│ │ [Kafka · L1 · Data] [Docker · L3 · Engineering]                          │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ┌─ Details ─────────────────────────────────────────────────────────────────┐ │
│ │ Role            Senior Backend Engineer                                   │ │
│ │ Status          done                                                      │ │
│ │ Salary          90k                                                       │ │
│ │ Visa            sponsored                                                  │ │
│ │ Created         2026-07-29 09:00                                          │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ┌─ Processing ──────────────────────────────────────────────────────────────┐ │
│ │ Execution     exec-1234    Status  completed                              │ │
│ │ ✓ Load Job          ✓ Analyze Job      ✓ Score Job                        │ │
│ │ ✓ Fetch Content     ✓ Extract Skills   ✓ Recommendation                   │ │
│ │ ✓ Extract Content   ✓ Summarize        ✓ Save Results                     │ │
│ │ ✓ Build Context                                                           │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ┌─ Description ─────────────────────────────────────────────────────────────┐ │
│ │ We need a senior backend engineer with Python, Postgres and Kafka.        │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

The `recommendation` badge maps apply → green, consider → blue, skip → gray.
Tagged skills render as compact badges; `missing`/`low` skills are tinted to
signal gaps. Full specs live in `docs/ux/features/jobs/`.

---

## UX Documentation

Full UX specs live under `docs/ux/` and are split into:

- `docs/ux/design-system/` — reusable primitives (Drawer, ...)
- `docs/ux/features/` — component/page specifications (Jobs page, Add Job, Processing Queue, ...)
- `docs/ux/flows/` — end-to-end user flows (browse, create, process live, ...)

See `docs/ux/README.md` for the full index.
