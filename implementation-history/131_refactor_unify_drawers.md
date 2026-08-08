# Prompt 131 - Unify Drawers on the shared vaul Drawer

## Objective

Unify every drawer in the application on the single vaul-based shared
`Drawer` primitive (`apps/frontend/src/shared/components/Drawer.tsx`),
with a **single default `lg` width** and **no per-drawer variant
overrides**, so all drawers share a consistent width. Fix the width bug
that caused the `lg` drawer to render ~335px instead of 720px, then
polish the Job Detail drawer UX and add a company status filter.

## Current State

- Some drawers used the legacy `Sheet` (`shared/ui/sheet.tsx`,
  `DrawerComponents`) instead of the unified vaul `Drawer`.
- Drawers overrode the shared `Drawer`'s `variant` (`xs` in the mobile
  sidebar, `full` in WorkflowTerminal and RuleFormDrawer), breaking the
  single-default-width design.
- The `lg` drawer rendered ~335px instead of 720px: the shadcn base in
  `shared/ui/drawer.tsx` carried `data-[vaul-drawer-direction=...]:w-3/4`
  and `sm:max-w-sm` classes that overrode `max-w-[720px]`.
- The shared `Drawer` default `variant` had drifted to `md`.

## Implementation Steps

## 1. Unify drawer usage

- `widgets/sidebar/index.tsx`: mobile nav drawer uses `placement="left"`
  with the default variant (no `variant="xs"` override).
- `shared/components/WorkflowTerminal.tsx` and
  `features/rules/components/RuleFormDrawer.tsx`: switch to the shared
  `Drawer`, drop the `variant="full"` override (RuleFormDrawer keeps
  `placement="bottom"`).
- `shared/components/Drawer.tsx`: default `variant = "lg"`.
- Delete the dead `shared/ui/sheet.tsx` (no remaining references).
- Verify no `<Drawer ... variant="...">` override remains anywhere.

## 2. Fix the width bug

- `shared/ui/drawer.tsx`: remove the data-scoped `w-3/4` and
  `sm:max-w-sm` classes from the base `DrawerContent` so the consumer's
  `max-w-[720px]` (from `DRAWER_VARIANTS.lg`) takes effect.

## 3. Job Detail drawer polish

- `features/jobs-v2/components/JobDetailDrawer.tsx`:
  - Swap section order: Tagged Skills moves before Processing.
  - Move Processing to the end of the drawer and wrap it in a
    `Collapsible` default-collapsed `ProcessingSection`.
  - Style the Recommendation section with `border-primary/20 bg-primary/5`
    (matching the company detail).
  - Add a score strip at the top (GradeBadge + colored JobScoreCard with
    Fit / Success / Overall), replacing the old 4-column muted grid.

## 4. Company status filter

- Backend: `companies_v2_router.py` — `status` query parameter filtered
  exactly via `_matches` against the shared `JobStatus` vocabulary
  (`created`, `pending`, `queued`, `processing`, `running`, `completed`,
  `processed`, `failed`, `cancelled`).
- Frontend:
  - `entities/company/types.ts` + `api.ts` + `hooks.ts`: `status` in
    `CompanySearchQuery`, `listInfinite`, `filterStatus` in
    `useCompaniesInfiniteQuery` (filterKey + clear + activeFilterCount).
  - `features/companies-v2/components/CompaniesToolbar.tsx`: Status Select
    with `STATUS_LABELS`, wired through `CompaniesPage` and
    `widgets/companies-page/index.tsx`.

## 5. Docs

- `docs/ux/design-system/drawer.md`: default `lg`, consumers must not
  override the variant; variants table no longer lists Processing Queue /
  Editors as `md`/`xl` usage; add Rule Form Drawer usage (placement
  bottom); Sheet references removed; add "Header Close Button Clearance"
  note about the deprecated Sheet-based drawers.
- `docs/ux/features/rules/rule-form-drawer.md`: placement `bottom`,
  default `lg` variant (no `variant="full"`).
- `docs/ux/app-shell.md`: mobile nav opens a left vaul Drawer (default
  `lg`), not a `Sheet`.
- `docs/ux/features/jobs/add-job.md`, `docs/ux/features/jobs/page.md`,
  `docs/ux/features/skills/page.md`, `docs/ux/features/companies/company-detail.md`,
  `docs/ux/features/companies/edit-company.md`: Sheet → shared vaul Drawer
  references.
- `docs/ux/features/companies/page.md`: Status Filter section + Controls
  table `[Status ▾]`.
- `docs/api/companies/list-companies.md`: `status` filter parameter.
- `docs/ux/flows/companies/browse-companies.md`: filter-by-status step.
- This file (`implementation-history/131_refactor_unify_drawers.md`).

---

# Testing Requirements

Backend:

    uv run pytest apps/backend/tests/companies/ -v

Frontend:

    cd apps/frontend && npx vitest run
    npm run typecheck

---

# Important Constraints

- Every drawer uses the default `lg` variant; only `placement` may vary.
- All AI/DB/UI conventions per AGENTS.md (LLMService only, ORM only,
  TypeScript only, per-context routers).
- No DB migration (no schema change for the status filter — `status` is an
  existing row column).
- No version bump (batched at release, per repo convention).
