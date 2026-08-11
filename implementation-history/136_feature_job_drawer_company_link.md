# Prompt 136 - Job drawer: company link to its detail drawer

## Objective

Make the company in the Job Details drawer both **selectable** (existing
company picker) and **linked to its detail drawer**: once a company is linked,
its name becomes a deep link to the company's detail drawer on the Companies
page, while a caret button keeps the change/unlink picker available.

## Current State

- The Job Details drawer's `Company` row uses `CompanyPicker`
  (`apps/frontend/src/features/jobs-v2/components/CompanyPicker.tsx`): a single
  ghost button labelled with the company name (or `Set company`) that opens a
  searchable picker popover backed by `GET /api/companies/list`.
- `CompanyPicker` had **no link** to the company detail drawer; the docs
  (`docs/ux/features/jobs/page.md`) already claimed the linked name was a deep
  link to `/companies?company=<id>`, but that was not implemented — a
  `JobDetailDrawer.test.tsx` test named "links the company name..." only
  asserted the picker button's text.

## Changes

- `apps/frontend/src/features/jobs-v2/components/CompanyPicker.tsx`:
  - When `companyId` and `companyName` are set, render the company name as an
    `<a href="/companies?company=<id>">` link (deep link to the Companies page,
    which opens its detail drawer) and shrink the trigger to a caret-only
    `Change company` button.
  - When no company is linked, keep the `Set company` picker button.
  - The picker popover, search and Unlink action are unchanged.
- `apps/frontend/src/features/jobs-v2/components/CompanyPicker.test.tsx`:
  - Added a test asserting the linked company name renders a link to
    `/companies?company=c-1`.
- `apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.test.tsx`:
  - Strengthened the "links the company name" test to assert the real link
    (`/companies?company=company-1`) plus the presence of the `Change company`
    picker button.
- `docs/ux/features/jobs/page.md`:
  - Documented the linked-name link + caret picker and the `Set company`
    unlinked state in "Job Details — Set Company"; updated the drawer layout
    wireframe (`Acme GmbH →▾`).

## Verification

Frontend:

    cd apps/frontend && npx vitest run   # 525 pass (60 files)
    npx tsc --noEmit                      # no new errors (42 pre-existing unrelated)

## Constraints

- No version bump (feature batched at release).
- The deep link uses a plain `<a>` to `/companies?company=<id>`, matching the
  existing pattern in `PublishedBySection` and the Companies page navigation.
- The picker (select/unlink) behavior is preserved alongside the new link.
