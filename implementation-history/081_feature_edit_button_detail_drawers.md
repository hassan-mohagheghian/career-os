# Prompt 081 - Edit Button in Company/Job Detail Drawers

## Objective

Add an **Edit** button to the Company Detail drawer and the Job Detail drawer
headers. Clicking it simply opens the existing **Edit Company** / **Edit Job**
drawer for the same entity — the button is a shortcut entry point alongside
the row-level Edit action. No new editing logic is introduced; the drawers are
already implemented and page-level state already exists.

## Current State

- `CompanyEditDrawer` (`features/companies-v2`) and `JobEditDrawer`
  (`features/jobs-v2`) are opened from the row Actions column via page-level
  `editCompanyId` / `editJobId` state (`CompaniesPage` / `JobsPage` receive
  `onEdit` and render the edit drawer).
- `CompanyDetailDrawer` and `JobDetailDrawer` headers render only a title; the
  detail drawers have no `onEdit` prop.

## Implementation Steps

1. `features/companies-v2/components/CompanyDetailDrawer.tsx`:
   - Add `onEdit?: (id: string) => void` to props; render a ghost **Edit**
     button (PencilSimple icon) in the SheetHeader when `onEdit` and
     `companyId` are present; calls `onEdit(companyId)`.
2. `features/companies-v2/components/CompaniesPage.tsx`: pass `onEdit={onEdit}`
   to `CompanyDetailDrawer`.
3. `features/jobs-v2/components/JobDetailDrawer.tsx`:
   - Add `onEdit?: (id: string) => void` to props; render the same header Edit
     button for `jobId`; import `Button` and `PencilSimple`.
4. `features/jobs-v2/components/JobsPage.tsx`: pass `onEdit={onEdit}` to
   `JobDetailDrawer`.

### Tests

5. `CompanyDetailDrawer.test.tsx`: new `CompanyDetailDrawer edit` suite —
   clicking "Edit company" calls `onEdit('company-1')`.
6. `JobDetailDrawer.test.tsx` (new): clicking "Edit job" calls `onEdit('job-1')`;
   the button is not rendered when `onEdit` is omitted.

### Docs

7. `docs/ux/features/companies/company-detail.md`: header wireframe + new
   "Header Actions" section for the Edit button.
8. `docs/ux/features/jobs/edit-job.md`: note the Job Details drawer header
   Edit button as an additional trigger.
9. `DESIGN.md`: Job Details Drawer and Company Detail Drawer wireframes show
   the `[Edit]` header action.

## Testing Requirements

- Frontend: `cd apps/frontend && npx vitest run` — 380 passed (47 files).
- `npx tsc --noEmit` — no errors in the changed files (baseline pre-existing
  errors only).

## Constraints

- Reuses the existing page-level edit state — no new drawer state or API
  calls; the detail drawer stays open underneath the edit drawer.
- Feature change → SemVer MINOR bump to **3.4.0** in all four version
  locations + `check-version.sh`.
