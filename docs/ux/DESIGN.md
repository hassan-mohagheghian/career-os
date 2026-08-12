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

Navigation is a **left sidebar rail** on desktop (`lg+`), collapsible to an
icon-only rail. On mobile (`<lg`) the rail collapses into a hamburger (top-left
of a slim top bar) that opens a left sheet with the same items.

```
SIDEBAR RAIL
  ├── Job Search (brand → /jobs)
  ├── Jobs           Job list (infinite scroll) + Processing Queue drawer
  ├── Companies      Company intelligence + processing queue
  ├── Skills         Skill management, aliases, insights
  ├── Candidate      Candidate profile import + review
  ├── Rules          Scoring rules configuration
  └── AI ▾           Inline expandable submenu
      └── LLM Configurations
  ──────────────────────────
  ├── Theme toggle   (bottom cluster)
  ├── Generation History (bottom cluster)
  └── Collapse toggle   (w-60 ⇄ w-[68px] icon rail, persisted)

MOBILE (<lg): hamburger → left Sheet with the same nav + bottom cluster.
```

Per-job detail pages (e.g. the Application Workspace at `/jobs/{id}/application`)
are reached from within the Jobs workspace — the rail highlights Jobs and the page
offers a "← Back to Job" link (`/jobs?job={id}`), which reopens the Job Details
drawer for that job.

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
│ # │ Pin │ Job                  │ Company    │ Location │ Scores        │ Proc.  │ Updated │
│─────────────────────────────────────────────────────────────────────────────────────│
│ 1 │ ●  │ Senior Backend Eng.  │ GetYourGuid│ Berlin   │ [A++] F 95 S 91 O 94 │ Ready  │ 2m      │
│ 2 │ ○  │ Backend Engineer     │ Karla      │ Berlin   │ [A+] F 90 S 88 O 90  │ Running│ now     │
│ 3 │ ○  │ Python Developer     │ Flexa      │ Remote   │ [A] F 86 S 84 O 83   │ Failed │ 5m      │
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

### Add Job Drawer (Create Entity — job mode)

```text
┌─────────────────────────────────────────────┐
│ Import Job                          [Close] │
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
│ ⚠ URL already exists.  Open existing job    │
├─────────────────────────────────────────────┤
│                    [Cancel] [Add] [Add & Queue]│
└─────────────────────────────────────────────┘
```

On duplicate URL (409) the error box adds an **Open existing job** link that
navigates to `/jobs?job=<id>` (id from `error.details.job_id`) and opens the
existing job's detail drawer.

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
│ Job Details                                            [Edit]         [Close]│
├───────────────────────────────────────────────────────────────────────────────┤
│ [B]  Fit 85   Success 70   Overall 79                [Why]               │
│                                                                              │
│ Senior Backend Engineer                                                      │
│ Company   Acme Inc →▾   │ Employment  Permanent                            │
│ Location  Berlin, DE…    │ Salary      90k                                  │
│ Work Types Hybrid, FT    │ Visa        EU Blue Ca… (hover/click → full)    │
│ Open job posting ↗                                                          │
│                                                                              │
│ ┌─ Recommendation ─────────────────────────────────────────────────────────┐ │
│ │ [consider]           2026-08-03 12:00                                    │ │
│ │ Great role overall. It matches the senior backend profile...             │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ┌─ Tagged Skills ──────────────────────────────────────────────────────────┐ │
│ │ [Python · L4 · Language] [Postgres · L4 · Data]                          │ │
│ │ [Kafka · L1 · Data] [Docker · L3 · Engineering]                          │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ┌─ AI Analysis ────────────────────────────────────────────────────────────┐ │
│ │ • Mention Kafka coursework                                               │ │
│ │ • Ask about salary band                                                  │ │
│ ├─ Summary ────────────────────────────────────────────────────────────────┤ │
│ │ Backend role at Acme.                                                    │ │
│ │ Resume fit: Strong fit.  Note: Apply early.                              │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ ▸ Published by — RecruitCo, TalentBridge GmbH                                │
│                                                                              │
│ ▸ Processing                                                                 │
│                                                                              │
│ ┌─ Description ─────────────────────────────────────────────────────────────┐ │
│ │ We need a senior backend engineer with Python, Postgres and Kafka.        │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

The `recommendation` badge maps apply → green, consider → blue, skip → gray.
The `[Why]` button after the Overall score opens a **Scores Explanation**
popover (Why it fits / Chance of success / Concerns). It auto-opens on hover,
auto-closes on unhover, and clicking pins/unpins it. Below the title a
balanced two-column block (each half the drawer width) shows six labeled rows,
three per column: `Company` (picker) / `Location` / `Work Types` on the left;
`Employment` / `Salary` / `Visa` on the right. Rows are aligned one-to-one
across the columns. `Location` and `Visa` are truncated at 30 characters with
an ellipsis; hovering reveals the full value in a tooltip and clicking
expands/collapses the value inline. Tagged skills render as compact badges;
`missing`/`low` skills are tinted to signal
gaps. The **Published by** section is a collapsed-by-default `Collapsible`
whose folded trigger shows the recruiter company names inline, positioned just
before the **Processing** collapsible. Full specs live in
`docs/ux/features/jobs/`.

---

### Rules Page

Each rule has a single `priority` (0–100) that drives list order, the severity
badge, and the LLM weight (`w:{n}`). Rules are grouped into scope columns.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Scoring Rules                                    (e.g. 17/20 active)          │
├──────────────────────────────────────────────────────────────────────────────┤
│ [All] [Shared] [Jobs] [Product Company] [Recruiting]                         │
├──────────────┬──────────────┬───────────────┬───────────────┬───────────────┤
│ SHARED Rules │  JOB Rules   │ Product Co... │ Recruiting... │               │
│ (4/4)        │  (7/7)       │   (5/5)       │   (4/4)       │               │
│ + Add rule   │ + Add rule   │ + Add rule    │ + Add rule    │               │
│ ⠿ key_name   │ ⠿ key_name   │ ⠿ key_name    │ ⠿ key_name    │               │
│  fit[Shared] │  fit[Job]    │  fit[Prod]    │  fit[Recr]    │               │
│  [Critical]  │  [High]      │  [Critical]   │  [Critical]   │               │
│  w:100 ⦿[↑][↓]│  w:85 ⦿[↑][↓]│  w:100 ⦿[↑][↓]│  w:100 ⦿[↑][↓]│               │
│  value text  │  value text  │  value text   │  value text   │               │
└──────────────┴──────────────┴───────────────┴───────────────┴───────────────┘
```

Priority badge legend: ≥90 Critical, ≥75 High, ≥50 Med, else Low. Move up/down
sets the rule to `neighbor ± 1` (clamped 0–100); drag redistributes the column.

### Add / Edit Rule Drawer

A right-side drawer (same side as every other drawer), `lg` width.

```text
                     ┌──────────────────────────────────────────────┐
                     │ Add Rule / Edit Rule                [Close] ✕│
                     ├──────────────────────────────────────────────┤
                     │ Scope ▼        Category ▼                    │
                     │ ┌───────────┐  ┌───────────┐                 │
                     │ │ Job ▾     │  │ Fit score ▾│                │
                     │ └───────────┘  └───────────┘                 │
                     │ Key name *      Priority (0-100)             │
                     │ ┌───────────┐  ┌───────────┐                 │
                     │ │ remote_work│  │ 50        │                 │
                     │ └───────────┘  └───────────┘                 │
                     │ Value / rule *                               │
                     │ ┌────────────────────────────────────────┐  │
                     │ │ How the rule matches candidates /       │  │
                     │ │ companies                               │  │
                     │ └────────────────────────────────────────┘  │
                     │ How this affects scoring (optional)          │
                     │ ┌────────────────────────────────────────┐  │
                     │ │ Optional description                   │  │
                     │ └────────────────────────────────────────┘  │
                     │                              [Cancel] [Save] │
                     └──────────────────────────────────────────────┘
```

Full specs: `docs/ux/features/rules/`.

---

### Companies Page

```text
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ Companies (128)                       Loaded 25 of 128      Queue           + Add Company│
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ Search ............................................        [Industry ▾] [Status ▾] [Pinned] [Columns] [Clear]│
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ # │ Pin │ Name │ Industry │ Location │ Size │ Jobs │ Scores │ Status │ Updated │ Created │ Actions │
│───│─────┼──────┼──────────┼──────────┼──────┼──────┼────────┼─────────┼─────────┼─────────┼─────────│
│ 1 │ ●  │ Acme │ Software │ Berlin   │ 1-50 │ 12   │ [A+] F 85 S 90 O 88 │ Completed │ 2m │ 2h │ ⋯ │
│ 2 │ ○  │ Acme │ Software │ Berlin   │ —    │ 0    │ [—] F — S — O — │ Completed │ 5m │ 1d │ ⋯ │
│ 3 │ ○  │ Inc  │          │          │      │      │ alias            │           │     │     │   │
│ 4 │ ○  │ Beta │ Fintech  │ Munich   │ 51-200│ 4    │ [B] F 60 S 55 O 58 │ Completed │ 5m │ 1d │ ⋯ │
│ ○  │ Head │ Recruit  │ Berlin   │ 1-50 │ 7¹  │ [—] F — S — O — │ Completed │ 5m │ 1d │ ⋯ │
│ ○  │ Nova │ Health   │ —        │ —    │ 0    │ [—] F — S — O — │ Failed   │ 1h │ 2d │ ⋯ │
│                                                                                          │
│                                       Loading more companies...                           │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

Alias companies render a small `alias` badge next to their name; selecting the
row opens the detail drawer where the relation can be managed.

The **Jobs** column is adaptive to company role: product companies show the
count of jobs they hire for (`12`), while recruiter-type companies
(`RECRUITING_AGENCY` / `STAFFING_COMPANY`) show the number of jobs they list
for clients (`7¹`, with a `"7 jobs listed for clients"` tooltip). Zero shows
`—`.

### Add Company Drawer (Create Entity — company mode)

```text
┌──────────────────────────────────────────────┐
│ + Add Company                          Close │
├──────────────────────────────────────────────┤
│ Primary Link *                               │
│ ┌──────────────────────────────────────────┐ │
│ │ https://acme.example                    │ │
│ └──────────────────────────────────────────┘ │
│ [Website]  [LinkedIn]                        │
│ Company Name (Optional)                      │
│ ┌──────────────────────────────────────────┐ │
│ │ Acme GmbH                               │ │
│ └──────────────────────────────────────────┘ │
│ Additional Links                     [+Add]  │
│   • https://acme.example · careers          │
│ Notes                                 [+Add] │
│   • Berlin product company                  │
├──────────────────────────────────────────────┤
│                [      Add      ] [Add&Process]│
└──────────────────────────────────────────────┘
```

### Company Detail Drawer

```text
┌────────────────────────────────────────────────────────────────┐
│ Company Details                                    [Edit] Close │
├────────────────────────────────────────────────────────────────┤
│ [A+]  Fit 85 · Success 90 · Overall 88                         │
│ ◉ Acme GmbH                                                    │
│ Software Development                                           │
│ Berlin, Germany · 51-200 · Product Company                      │
│ 12 jobs                                                        │
│ ◈ Related Companies                                  [ Manage ]│
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Recommendation: A — apply via careers page                 │ │
│ └────────────────────────────────────────────────────────────┘ │
│ Recruiter for 3 jobs (recruiter-type companies only)           │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Acme GmbH                                    2 jobs        │ │
│ │   • Senior Backend Engineer   → job drawer                 │ │
│ │   • Platform Engineer         → job drawer                 │ │
│ │ Beta GmbH                                    1 job         │ │
│ │   • Data Engineer             → job drawer                 │ │
│ └────────────────────────────────────────────────────────────┘ │
│ Company Overview                                              │
│ Intelligence sections (importance order)                      │
│ Scores explanation (Why popover next to header score cards)   │
│ Linked Jobs                                              │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 2 linked jobs                                          │ │
│ │ Senior Backend Engineer                    [B]         │ │
│ │   Berlin · [Fit 84][Success 63][Overall 76]           │ │
│ │ Platform Engineer                          [A]         │ │
│ │   Munich · [Fit 90][Success 70][Overall 82]           │ │
│ └────────────────────────────────────────────────────────┘ │
│ Notes & Links (read only)                                     │
│ [View All Jobs] [Website]        [Reprocess] [Delete]         │
└────────────────────────────────────────────────────────────────┘
```

The job-count badge in the header is adaptive like the list's Jobs column:
product companies show `N jobs` (hiring count); recruiter-type companies
(`RECRUITING_AGENCY` / `STAFFING_COMPANY`) show `N listed` (jobs listed for
clients, matching the "Recruiter for N jobs" section below).

### Relate Company Dialog

Opened via `Manage` in the Related Companies section of the Company Detail
drawer. Relating an alias re-points its jobs onto the chosen main.

```text
┌──────────────────────────────────────────────────────────────┐
│ Related Companies                                      Close │
├──────────────────────────────────────────────────────────────┤
│ Relate <current company> to a main company. Jobs linked to   │
│ an alias are re-pointed to the main company.                 │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ [alias of] Acme GmbH                            [Remove] │ │ ← alias only
│ └──────────────────────────────────────────────────────────┘ │
│ Search companies...                                          │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ ◉ Acme GmbH                                      2 alias │ │
│ │ ◉ Beta GmbH                                             │ │
│ └──────────────────────────────────────────────────────────┘ │
│                              [Cancel]          [Set as Main] │
└──────────────────────────────────────────────────────────────┘
```

### Processing Drawer (Companies)

The Companies page opens the **shared** Processing Drawer with
`targetType="company"` (same drawer as Jobs, filtered to companies). It is fed
by `GET /api/processing/queue` and live SSE.

```text
┌──────────────────────────────────────────────┐
│ Processing Queue                      Close │
├──────────────────────────────────────────────┤
│ Running (1)                                  │
│ ┌──────────────────────────────────────────┐ │
│ │ Acme GmbH                                │ │
│ │ Step: analyze · ▒▒▒▒░░ 60% · 🗙 Cancel   │ │
│ │ └─ Workflow step tree (live SSE)         │ │
│ └──────────────────────────────────────────┘ │
│ Waiting (2)                                  │
│ ┌──────────────────────────────────────────┐ │
│ │ Beta GmbH                                │ │
│ │ queued · ▶ Start · 🗑 Remove             │ │
│ └──────────────────────────────────────────┘ │
│ Failed (1)                                   │
│ ┌──────────────────────────────────────────┐ │
│ │ Nova                                     │ │
│ │ failed: timeout · ⟳ Retry · 🗑 Remove    │ │
│ └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

The Companies workspace is parity with the Jobs v2 UX (virtualized table,
infinite scroll, Sheet drawers). Company processing runs through the shared
`ProcessingExecution` / SSE lifecycle (context preparation without LLM, then a
single-LLM analysis), monitored via the shared Processing Drawer filtered to
companies. Full specs live in `docs/ux/features/companies/`.

---

### Skills Page

The Skills page is parity with the Jobs/Companies v2 UX (virtualized table,
infinite scroll, Sheet drawers). It replaces the legacy SkillsTab.

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ </> Skills (128)                     Loaded 25 of 128           + Add Skill   │
├───────────────────────────────────────────────────────────────────────────────┤
│ Search .........................                     [Category ▾] [Pinned] [Columns] │
│ # │ Select │ Pin │ Name              │ Category   │ Lv │ Roles     │ Demand │ Conf │ Created │
│───│─────── │─────│───────────────────│────────────│────│───────────│────────│──────│─────────│
│ 1 │ ☐      │ ●  │ Kubernetes 2 aliases│ engineering│ 4  │ DevOps    │ 90%    │ 85%  │ 2m      │
│ 2 │ ☐      │ ○  │ Kafka             │ technical  │ 2  │ Data      │ 70%    │ 60%  │ 5m      │
│ 3 │ ☐      │ ○  │ DDD               │ domain     │ 3  │ Backend   │ —      │ 45%  │ 1h      │
│                                                                               │
│                                        Loading more skills...                 │
└───────────────────────────────────────────────────────────────────────────────┘
```

When rows are selected the toolbar shows a bulk action bar:

```text
│ Search .........................                     [Category ▾] [Pinned] [Columns] │
│ 2 selected   [⟳ Merge 2 into...]   [Clear]                                       │
```

The Row number, Select and Pin columns are toggled via the Columns dropdown;
merging selected skills into one target reuses the single-merge target picker
dialog. Rows highlight on hover (and while any inner control has focus) with a
muted background and inset ring.
```

### Skill Detail Drawer

```text
┌────────────────────────────────────────────────────────────┐
│ </> Kubernetes (engineering)                       ✕  Edit │
├────────────────────────────────────────────────────────────┤
│ ★ Lv.4   Confidence: 85%   Market: 90%                    │
│ ┌─ Relevant Roles ──────────────────────────────────────┐  │
│ │ DevOps, SRE, Platform                                  │  │
│ └────────────────────────────────────────────────────────┘  │
│ ┌─ Path ────────────────────────────────────────────────┐  │
│ │ Container orchestration → service mesh → ...          │  │
│ └────────────────────────────────────────────────────────┘  │
│ ┌─ Tags ────────────────────────────────────────────────┐  │
│ │ [kubernetes] [helm] [istio]                            │  │
│ └────────────────────────────────────────────────────────┘  │
│ ┌─ Also Known As ───────────────────────────────────────┐  │
│ │ [k8s]                                                  │  │
│ └────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────┤
│          [✂ Break down]                    [🗑 Delete]     │
└────────────────────────────────────────────────────────────┘
```

### Add Skill Drawer

```text
┌────────────────────────────────────────────────┐
│ Add Skill                            ✕         │
├────────────────────────────────────────────────┤
│ Name                                        *  │
│ [......................................]      │
│ Level / Category / Relevant Roles / Path      │
│ [Cancel]                          [Add Skill] │
└────────────────────────────────────────────────┘
```

The Skills workspace is parity with the Jobs v2 UX (virtualized table, infinite
scroll, Sheet drawers). Full specs live in `docs/ux/features/skills/` and
`docs/ux/flows/skills/`.

### Candidate Profile Import Page

The Candidate module (110 Phase 1) starts with **Profile Import**: import
resume/LinkedIn sources, run AI analysis, and review the canonical profile.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Candidate Profile                                    [nav: Candidate]    │
├──────────────────────────────────────────────────────────────────────────┤
│ [Sources] [Review]                                                       │
├──────────────────────────────────────────────────────────────────────────┤
│ [SOURCES TAB]                                                            │
│ ┌──────────────────────────┐  ┌──────────────────────────┐              │
│ │ RESUME                   │  │ LINKEDIN                 │              │
│ │ textarea ┌──────────────┐│  │ textarea ┌──────────────┐│              │
│ │          └──────────────┘│  │          └──────────────┘│              │
│ │ [Save Resume]            │  │ [Save Profile]           │              │
│ │ Last updated 5m ago · v2 │  │ Last updated 3d ago · v1 │              │
│ │ [👁 View]                │  │ [👁 View]                │              │
│ └──────────────────────────┘  └──────────────────────────┘              │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ GITHUB (optional — placeholder)    [username..............]        │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ [✨ Analyze Profile]  [☑ Processing]   (queues candidate analysis │  │
│ │  when a resume/LinkedIn is pending; otherwise info toast "no new  │  │
│ │  version"; Processing opens queue drawer for candidate runs)      │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│ [REVIEW TAB]                                                           │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ PROFILE SUMMARY    name · title · version · location               │  │
│ │ [2 skills] [1 experience] [1 project] [1 education] [1 language]   │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────┐  ┌──────────────────────────┐              │
│ │ CONNECTED SOURCES        │  │ VERSION HISTORY          │              │
│ │  resume v2 [pending] 5m  │  │  v2 "added linkedin"     │              │
│ │   [👁 View]              │  │  v1 "initial import"     │              │
│ │  linkedin v1 [processed] │  └──────────────────────────┘              │
│ │   3d [👁 View]           │                                           │
│ └──────────────────────────┘                                           │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ SKILLS   [Python L4 96%] [PostgreSQL L4 90%] ...                  │  │
│ ├────────────────────────────────────────────────────────────────────┤  │
│ │ EXPERIENCE  role · company · dates · summary                      │  │
│ ├────────────────────────────────────────────────────────────────────┤  │
│ │ PROJECTS  name · description · url                                 │  │
│ └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

Profile analysis is a background workflow (`CANDIDATE_PROCESSING` execution,
SSE progress); the Review tab refetches `/profile`, `/sources` and `/versions`
after analysis. Analyze only queues a run when a resume/LinkedIn source is still
pending; otherwise it returns `status=noop` and the UI shows an info toast
(persisting a new version requires saving a new source first). Full specs live in
`docs/ux/features/candidate/profile-import.md` and
`docs/ux/flows/candidate/import-profile.md`.

### Job Application Workspace

The Applications module (140) adds a per-job Application Workspace at
`/jobs/{job_id}/application` (entry: airplane action on a job row, or the
**Application** button in the Job Details drawer header). It is a consumer of
existing intelligence — preparation, tailored resume and cover letter are generated
asynchronously (`application_preparation` / `application_resume` /
`application_cover_letter` executions) with SSE progress.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Back to Job                                          [Open job posting]│
│ Staff Engineer · Acme GmbH · Berlin                                      │
│ [Recommended] [Apply]             [A+] [Fit 85] [Success 88] [Overall 90]│
├──────────────────────────────────────────────────────────────────────────┤
│ ▸ AI generation in progress ▸ 42% · "Generating tailored resume"        │  ← SSE card
├──────────────────────────────────────────────────────────────────────────┤
│ APPLICATION                                                            │
│  Status [Recommended ▾]    Applied at [ 2026-08-11 ]                     │
│  FOLLOW-UPS  ☑ Follow up after interview · Sep 1  [🗑]  [note][📅][Add]  │
├──────────────────────────────────────────────────────────────────────────┤
│ PREPARATION                                                        [⚡ Gen]│
│  Hard: [Kubernetes Missing] [Kafka Low high]  ·  Soft: [Comms low]       │
├──────────────────────────────────────────────────────────────────────────┤
│ DOCUMENTS                                                               │
│ ┌──────────────────────────┐  ┌──────────────────────────┐              │
│ │ TAILORED RESUME v2       │  │ COVER LETTER v1          │              │
│ │ [copy][↓][✎][🗑][Regen]   │  │ [copy][↓][✎][🗑][Regen]   │              │
│ └──────────────────────────┘  └──────────────────────────┘              │
└──────────────────────────────────────────────────────────────────────────┘
```

Empty state (no application yet): centered "No application yet" + `[Create Application]`
→ `POST /api/applications` (status `recommended`). Full specs live in
`docs/ux/features/applications/` and `docs/ux/flows/applications/`.

---

## UX Documentation

Full UX specs live under `docs/ux/` and are split into:

- `docs/ux/design-system/` — reusable primitives (Drawer, ...)
- `docs/ux/features/` — component/page specifications (Jobs page, Add Job, Processing Queue, ...)
- `docs/ux/flows/` — end-to-end user flows (browse, create, process live, ...)

See `docs/ux/README.md` for the full index.
