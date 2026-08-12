# Prompt 152 - Restructure Drawer Header Action Buttons

## Objective

Align the Company Detail and Job Detail drawers: move the company's website /
links to the top of the content (next to the score strip), move "Reprocess" into
the drawer headers beside "Edit", drop the company drawer's bottom footer
(View All Jobs / Delete), and add a matching Reprocess button to the Job Detail
drawer header so both drawers expose the same header actions.

## Current State

- `apps/frontend/src/features/companies-v2/components/CompanyDetailDrawer.tsx`:
  - Bottom footer (was lines ~488–523) holds View All Jobs, Website, Reprocess,
    Delete; header actions only contain Edit (line 233).
  - The drawer accepts `onDelete` and `onViewAllJobs` props (lines 198, 205) and
    already has `onReprocess` (line 197).
- `apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.tsx`:
  - Props are `jobId`, `onOpenChange`, `onEdit` (lines 45–49); no reprocess.
  - Header actions render `[Application] [Edit]` in `flex items-center gap-1`
    (lines 655–680).
  - Content top row already uses the `flex justify-between` pattern with "Open
    job posting" on the right (lines 483–513) — the pattern the Company drawer
    copies.
  - `Repeat` icon from `@phosphor-icons/react` not imported (imports lines
    11–22).
- Callers:
  - `apps/frontend/src/features/companies-v2/components/CompaniesPage.tsx:186`
    and `widgets/companies-page/index.tsx:167` pass the removed props; the
    widget wires `reprocessMutation` → `onReprocess` (lines 70–80, 140).
  - `apps/frontend/src/features/jobs-v2/components/JobsPage.tsx:47` exposes
    `onProcessV2: (id: string) => void` and passes it to the table
    (line 181); the drawer is rendered at lines 200–204 with only `onEdit`.
  - `apps/frontend/src/widgets/jobs-page-v2/index.tsx` defines
    `handleProcessV2` (lines 59–64, `processMutation` + opens queue drawer +
    bumps `queueReloadKey`) and passes `onProcessV2={handleProcessV2}`
    (line 164).
  - `apps/frontend/src/features/jobs-v2/components/JobActions.tsx:59` already
    renders a Reprocess row action wired to `onProcessV2`.
- `apps/frontend/src/features/companies-v2/components/CompanyJobsTab.tsx:14`
  declares an unused `onViewAllJobs` prop.

## Changes

1. `CompanyDetailDrawer.tsx` (company part — already implemented in working
   tree): wrap the score strip and the link column in `flex justify-between`;
   header renders a Reprocess ghost button (aria-label "Reprocess company",
   `Repeat` icon) before Edit, both driven by `companyId`; drop the footer and
   the `onDelete` / `onReprocess` / `onViewAllJobs` content props; remove the
   `Trash` import.
2. `JobDetailDrawer.tsx` (new — this task):
   - Add `onReprocess?: (id: string) => void` to `JobDetailDrawerProps`.
   - Import `Repeat` from `@phosphor-icons/react`.
   - In the header actions (before the Application button), add a ghost Reprocess
     button mirroring the company drawer's: `variant="ghost" size="sm"
     className="h-7 gap-1 text-xs text-muted-foreground"`, `Repeat` icon +
     "Reprocess", `aria-label="Reprocess job"`, `onClick={() => onReprocess?.(
     jobId)}`, rendered only when `onReprocess && jobId`.
3. `JobsPage.tsx` — accept `onReprocess: (id: string) => void` in the props
   (add to interface line ~51 + destructure line ~85), and pass
   `onReprocess={onReprocess}` to `JobDetailDrawer` (line ~200). The widget
   already passes `onProcessV2`; wire the drawer from reusing that same handler
   (see step 4).
4. `widgets/jobs-page-v2/index.tsx` — pass `onReprocess={handleProcessV2}` to
   `JobsPageContent` (reuses the existing process/reprocess mutation + queue
   drawer flow, symmetric with company reprocess which opens the queue drawer).
5. `CompaniesPage.tsx` — remove the `onViewAllJobs` prop (interface +
   destructure + drawer usage); stop passing `onDelete` to the drawer (row-level
   delete via `CompaniesTable` unchanged).
6. `widgets/companies-page/index.tsx` — remove `navigateToJobs` and
   `onViewAllJobs={navigateToJobs}`.
7. `CompanyJobsTab.tsx` — drop the unused `onViewAllJobs` prop.
8. Docs (rule 13): `docs/ux/features/companies/company-detail.md`,
   `docs/ux/features/companies/page.md`, `docs/ux/features/jobs/page.md` (jobs drawer header actions),
   `docs/ux/DESIGN.md`, `docs/ux/flows/companies/browse-companies.md`,
   `docs/ux/README.md` index.

## Testing Requirements

- `CompanyDetailDrawer.test.tsx`: remove the `onDelete` prop from the render
  helper; add tests for the header Reprocess button calling `onReprocess`, the
  Website link at top with `href`/`target=_blank`, the other `company.links`
  listed beneath it (skip the link equal to the website), and absence of View All
  Jobs / Delete buttons.
- `JobDetailDrawer.test.tsx`: extend the render helper (`renderDrawer`, line 48)
  with an `onReprocess` parameter; add a test that clicking the header button
  named "Reprocess job" calls `onReprocess('job-1')`; add a test that the button
  is absent when `onReprocess` is not provided.
- Run `cd apps/frontend && npx vitest run`, `npm run lint`, `npm run typecheck`.

## Constraints

- Respect AGENTS.md rule 13 (UX docs + wireframes updated) and rule 10
  (no `entrypoints/api.py` changes) — frontend-only change, no backend.
- Keep the linked-jobs per-row "Open job drawer"/"Go to Jobs page" actions.
- Reuse the existing process mutation flow for jobs (no new endpoints); the
  reprocess button is a duplicate entry point for `onProcessV2`, consistent with
  how the companies page exposes reprocess from both the row and the header.