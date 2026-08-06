# Prompt 082 - Fix Company Link in Job Detail Drawer

## Objective

Make the company link in the Job Detail drawer actually open the company
detail drawer. Previously the link was dead: its `onClick` called
`e.preventDefault()` and `setSearchParam('company', id)`, which only rewrites
the current page's URL (`history.replaceState`) — it never navigates and never
opens the drawer. The intended behavior (documented in
`docs/ux/features/companies/relate-company.md`) is a deep link to
`/companies?company=<id>`, where `CompaniesPageAdapter` opens the detail
drawer on mount.

## Current State

- `JobDetailDrawer.tsx` renders the company name as a primary-colored link
  with `href="/companies?company=<id>"` but blocks navigation in `onClick`.

## Implementation Steps

1. `features/jobs-v2/components/JobDetailDrawer.tsx`:
   - Remove the `onClick` prevent-default handler and the `setSearchParam`
     import; let the anchor navigate to `/companies?company=<id>`.
2. `JobDetailDrawer.test.tsx`:
   - Add `company_id` to the sample detail; new test asserting the company
     link has `href="/companies?company=company-1"`.

## Testing Requirements

- Frontend: `npx vitest run` — 381 passed (48 files, +1 new test).
- `npx tsc --noEmit` — no errors in the changed file.

## Constraints

- Bug fix → SemVer PATCH bump to **3.4.1** in all version locations +
  `check-version.sh`.
