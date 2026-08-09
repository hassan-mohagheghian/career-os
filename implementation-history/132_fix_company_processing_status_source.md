# Prompt 132 - Derive company processing status from the latest execution (same as jobs)

## Objective

Make the company **processing status** behave exactly like the job one — in
both the **status filter** and the **list** — by deriving it from the latest
`processing_execution` row instead of the company row's own (stale) `status`
column, and make sure both company and job show the correct state.

## Current State

Jobs v2 (`jobs_v2_router.py`) already derive the row status from the latest
execution: `job_status = latest_execution.status`, filter via
`exec_repo.target_ids_with_status("job", ...)` / `target_ids("job")` for
`none`, and display the shared `StatusBadge`.

Companies v2 (`companies_v2_router.py`) instead read the company row's
`status` column (`_matches` filter + `processing.status` in the list item).
That column is stale/partial: it is only ever set to `created` / `queued` /
`processed` (`company_service.persist_analysis` writes `processed`, the intake
flow writes `created`), and it is never updated to `running` / `failed` /
`cancelled` when the execution lifecycle changes. As a result a company with a
running/failed/cancelled execution wrongly shows `Queued` (or `Pending`), and
the filter cannot find those states.

The docs (`docs/ux/features/companies/page.md`, `company-row.md`) already
describe the intended behavior ("Processing status from the latest processing
execution") — the code never matched it.

## Implementation Steps

## 1. Backend — derive status from the latest execution

- `apps/backend/companies/presentation/api/companies_v2_router.py`
  - `list_companies_v2`: build `status_lookup = exec_repo.latest_statuses("company")`
    once, before filtering.
  - `_matches(...)`: filter on the execution-derived status
    (`status_lookup.get(row["id"])`). Support `status="none"` (company has no
    execution at all) matching the jobs `processing_status=none` semantics.
  - `_to_list_item(...)`: set `processing.status` from the latest execution's
    status (null when there is no execution), keeping `current_node`,
    `progress_pct`, `error` from the row.
  - `_build_company_detail(...)`: add `get_processing_execution_repo` and set
    the detail `status` from the latest execution as well, so the API is
    consistent between list and detail.
- No schema change, no migration.

## 2. Frontend — align filter and badge with jobs

- `features/companies-v2/components/CompaniesToolbar.tsx`: status filter
  options become the execution vocabulary exactly as the jobs toolbar:
  `created`, `queued`, `running`, `completed`, `failed`, `none` ("Not
  processed"). Drop the row-status vocabulary (`pending`, `processing`,
  `processed`, `cancelled`).
- `features/companies-v2/components/CompanyRow.tsx`: render the shared
  `StatusBadge` from `features/jobs-v2` (the exact badge jobs use) with the
  execution-derived status; delete the now-dead
  `CompanyProcessingBadge.tsx`.

## 3. Tests

Backend (`apps/backend/tests/companies/presentation/api/test_companies_v2_api.py`):

- Rewrite `test_status_filter` to seed `ProcessingExecutionModel` rows and
  filter by execution status (`completed`, `running`, ...), plus `none`.
- Update `test_scores_and_processing_shape` so `processing.status` comes from
  an execution (not the row).
- Assert `processing.status` is null when a company has no execution.
- Assert list + detail `status` both come from the latest execution.

Frontend:

- `CompaniesToolbar.test.tsx`: update the "reports a selected status" test to
  the new option set.
- `CompanyRow.test.tsx`: add a status badge assertion using the shared
  `StatusBadge` labels.

## 4. Docs

- `docs/api/companies/list-companies.md`: status filter uses the execution
  vocabulary (`created`, `queued`, `starting`, `running`, `completed`,
  `failed`, `cancelled`) plus `none`, exact match against the latest
  `processing_execution`.
- `docs/ux/features/companies/page.md`: Status Filter option list + the Status
  column section (execution vocabulary, shared `StatusBadge`), toolbar
  wireframe `[Status ▾]`.
- `docs/ux/features/companies/company-row.md`: Status column — latest
  processing execution, shared `StatusBadge`, vocabulary table.
- `docs/ux/flows/companies/browse-companies.md`: filter-by-status wording.
- This file (`implementation-history/132_fix_company_processing_status_source.md`).

---

# Testing Requirements

Backend:

    uv run pytest apps/backend/tests/companies/ -v

Frontend:

    cd apps/frontend && npx vitest run
    npm run typecheck

---

# Important Constraints

- Status semantics must match jobs: single source of truth is the latest
  `processing_execution` (ExecutionStatus vocabulary), never the company row
  `status` column.
- All AI/DB/UI conventions per AGENTS.md (ORM only, per-context routers,
  TypeScript only).
- No DB migration (no schema change).
- No version bump (batched at release, per repo convention).

---

# Part 2 — Job Details drawer: scores-explanation popover, Published-by & layout polish

## Objective

Rework the Job Details drawer's information layout and move the Scores
Explanation into a hover/click popover anchored to a `[Why]` button on the
score strip.

## Current State

The Job Details drawer stacked large sections vertically:

- `Details` and `Tagged Skills` (previously merged into one two-column row).
- `Published by` rendered as a full expanded box in the middle of the drawer.
- `Scores Explanation` rendered inline inside the `AI Analysis` section.

## Implementation Steps

### 1. Frontend — `apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.tsx`

- **Scores explanation popover**
  - Extract the fit / success / concerns lists into a reusable
    `ScoresExplanationBody` component.
  - Add `ScoresExplanationButton`: a `[Why]` ghost button placed right after
    the **Overall** score card on the score strip, using the shared
    `Popover`/`PopoverTrigger`/`PopoverContent`.
    - Hover opens the popover, unhover closes it.
    - Clicking toggles a "pinned" open state; clicking again closes it.
    - Content is a `Scores Explanation` panel listing *Why it fits*,
      *Chance of success* and *Concerns*.
  - Remove the inline `Scores Explanation` section from `AnalysisSection`
    (now surfaced via the popover only).
- **Published by**
  - New `PublishedBySection` component — a `Collapsible` **collapsed by
    default**; the folded trigger shows the recruiter company names inline
    (`▸ Published by — RecruitCo, TalentBridge GmbH`).
  - Expanded content keeps the recruiter links, company-type badges and
    extraction reasons.
  - Moved from the middle of the drawer to the end, just before
    `ProcessingSection`.
- **Header layout** (score strip / title / company / salary+visa)
  - Score strip now shows `[GradeBadge] Fit Success Overall` followed by the
    `[Why]` button, with the *Open job posting* link pushed right.
  - Title, `CompanyPicker`, location/meta on the left; Salary + Visa as
    `DetailRow`s on the right.
- New import: `Question` icon, `Popover` primitives.

### 2. Tests — `apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.test.tsx`

- Company-name test now asserts the `Change company` picker button contains
  the linked company name (the name is no longer a standalone link).
- Published-by test clicks the collapsed trigger before asserting the
  recruiter link / agency badge / reason are visible.
- New describe block *scores explanation*:
  - clicking `Show scores explanation` reveals the factors/concerns lists;
  - button is absent when the job has no analysis.

### 3. Docs

- `docs/ux/features/jobs/page.md`: updated Job Details drawer wireframe,
  score-strip bullet (with `[Why]` popover behavior), and the *Published by*
  section (collapsed `Collapsible` at the end, folded trigger shows names).
- `DESIGN.md`: Job Details Drawer wireframe + notes updated accordingly.
- This file (`implementation-history/132_fix_company_processing_status_source.md`).

## Testing Requirements

    cd apps/frontend && npx vitest run src/features/jobs-v2/components/JobDetailDrawer.test.tsx

## Important Constraints

- No version bump (batched at release).
- TypeScript only; reuse shared UI primitives (`Popover`, `Collapsible`).
- Docs (ASCII wireframe) updated for every UI change per AGENTS.md.

---

# Part 3 — Job Details header: balanced two-column labeled layout + Visa truncation

## Objective

Balance the two columns below the job title so each takes half the width and
holds exactly **three labeled rows**, moving one item into the right column,
and truncate the Visa value at 30 characters with a hover tooltip showing the
full value.

## Current State

The header block after the title used a `grid grid-cols-2` where the left
column held the `CompanyPicker` plus icon-only meta (location, work types,
employment types) and the right column held Salary + Visa. Only two right
rows, and the meta items had no labels.

## Implementation Steps

### 1. Frontend — `apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.tsx`

- Rebuild the two-column block as a `grid grid-cols-2 gap-4` with **3 labeled
  rows per column**:
  - Left column: `Company` (picker), `Location`, `Work Types`.
  - Right column: `Employment`, `Salary`, `Visa` (employment types moved from
    the left meta row to the right column to balance 3/3).
- `DetailRow` gains an optional `valueTitle` prop rendered as the native
  `title` attribute for hover tooltips.
- Visa value renders inside `inline-block max-w-[30ch] truncate`, so it is
  capped at ~30 characters with an ellipsis; the full value is shown on hover
  via `title`.
- Remove the now-unused icon imports (`MapPin`, `Briefcase`,
  `Clock as ClockIcon`); the icon-only meta row is gone.

### 2. Docs

- `docs/ux/features/jobs/page.md`: header wireframe updated — six labeled
  rows split 3/3 (Company / Location / Work Types | Employment / Salary /
  Visa), Visa truncated at 30 chars with hover tooltip.
- `DESIGN.md`: Job Details Drawer header row updated accordingly.
- This file (`implementation-history/132_fix_company_processing_status_source.md`).

## Testing Requirements

    cd apps/frontend && npx vitest run src/features/jobs-v2/components/JobDetailDrawer.test.tsx

## Important Constraints

- No version bump (batched at release).
- TypeScript only; reuse shared UI primitives.
- Docs (ASCII wireframe) updated for every UI change per AGENTS.md.

---

# Part 4 — Truncated Location/Visa with click+hover reveal; aligned two-column rows

## Objective

Truncate the **Location** value (like Visa) at 30 characters, let the user see
the full value via **hover or click** for both fields, and make the six header
rows align one-to-one between the two columns.

## Current State

- Location rendered as a plain string; only Visa was truncated (native
  `title` hover only, no click).
- The left column's `Company` row used a bespoke flex markup while the other
  five rows used `DetailRow`, so heights/rows did not justify exactly across
  the two columns.

## Implementation Steps

### 1. Frontend — `apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.tsx`

- **New `TruncatedValue` component**
  - Renders the value (fallback `—`) inside a `Tooltip` wrapped in a local
    `TooltipProvider` (Radix requires a provider; the test harness has none).
  - Truncated at `max-w-[30ch]` with ellipsis.
  - **Hover** shows the full value via `TooltipContent` (max-w-xs, wraps).
  - **Click** toggles inline expansion (`whitespace-normal break-words`) and
    collapses again on second click.
- **Use `TruncatedValue` for both `Location` and `Visa`** rows.
- **Uniform rows for alignment**: the `Company` row now uses the same
  `DetailRow` as the other five rows (label left, value right, `py-1.5`), so
  `Company↔Employment`, `Location↔Salary`, `Work Types↔Visa` sit at the same
  vertical baseline in the two-column grid.

### 2. Docs

- `docs/ux/features/jobs/page.md`: header wireframe note updated — Location
  also truncated at 30 chars; both Location and Visa reveal the full value on
  hover (tooltip) or click (inline expand); rows aligned one-to-one across the
  two columns.
- `DESIGN.md`: Job Details Drawer header row updated accordingly.
- This file (`implementation-history/132_fix_company_processing_status_source.md`).

## Testing Requirements

    cd apps/frontend && npx vitest run src/features/jobs-v2/components/JobDetailDrawer.test.tsx

## Important Constraints

- No version bump (batched at release).
- TypeScript only; reuse shared UI primitives (`Tooltip`, `TooltipProvider`).
- Docs (ASCII wireframe) updated for every UI change per AGENTS.md.

---

# Part 5 — Unify score order + color across job/company list and detail

## Objective

Make the score **order** and **colors** identical between list and detail for
both jobs and companies, by extracting one shared `scoreColor` helper and one
canonical score order.

## Current State (inconsistent)

| Surface | Order | Color thresholds |
| ------- | ----- | ---------------- |
| Job list (`JobRow`) | `O F S` | ≥90 green, ≥70 emerald, ≥50 yellow, ≥30 orange, <30 red |
| Job detail (`JobScoreCard`) | `Fit Success Overall` | ≥80 emerald, ≥60 blue, ≥40 yellow, <40 red |
| Company list (`CompanyRow`) | `F S O` | same as job list |
| Company detail (`CompanyScoreCard`) | `Fit Success Overall` | same 4-tier as job detail |

The 4-tier scheme (blue) only exists in the two detail drawers; the two list
rows already agree on a 5-tier scheme. Order differs only in `JobRow`.

## Implementation Steps

### 1. Shared helper — `apps/frontend/src/shared/lib/grade.ts`

- Add `export function scoreColor(value: number | null | undefined): string`
  with the canonical 5-tier mapping: `≥90 green`, `≥70 emerald`, `≥50 yellow`,
  `≥30 orange`, `<30 red`; null/undefined → `text-muted-foreground`.

### 2. Consume the shared helper

- `apps/frontend/src/features/jobs-v2/components/ScoreBadge.tsx`: drop the
  local `scoreColor`, import from `@/shared/lib/grade`.
- `apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.tsx`
  (`JobScoreCard`): drop the local 4-tier `scoreColor`, use the shared helper.
- `apps/frontend/src/features/companies-v2/components/CompanyScoreCard.tsx`:
  drop the local 4-tier `scoreColor`, use the shared helper.

### 3. Canonical order — Fit, Success, Overall

- `apps/frontend/src/features/jobs-v2/components/JobRow.tsx`: render the three
  `ScoreBadge`s as `F`, `S`, `O` (was `O`, `F`, `S`). Company list + both
  detail drawers already use Fit/Success/Overall.

### 4. Docs

- `docs/ux/features/jobs/job-row.md`: example `[A+] O 91 F 94 S 88` →
  `[A+] F 94 S 88 O 91`; Displayed Information list + score bullets reordered
  Fit → Success → Overall.
- `docs/ux/features/jobs/page.md`: score-strip bullet updated to the shared
  5-tier color scheme; wireframe row `Overall 79 Fit 85 Success 70` →
  `Fit 85 Success 70 Overall 79`.
- `DESIGN.md`: Job Details Drawer wireframe + notes updated to Fit / Success /
  Overall order and shared colors.
- This file (`implementation-history/132_fix_company_processing_status_source.md`).

## Testing Requirements

    cd apps/frontend && npx vitest run src/features/jobs-v2 src/features/companies-v2
    cd apps/frontend && npx tsc --noEmit

## Important Constraints

- No version bump (batched at release).
- TypeScript only; reuse the shared helper (no duplicated color logic).
- Docs (ASCII wireframe) updated for every UI change per AGENTS.md.
