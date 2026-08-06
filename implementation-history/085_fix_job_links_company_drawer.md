# Prompt 085 - Fix Job Links in Company Detail Drawer

## Objective

Job links in the Company Detail drawer were broken: clicking a linked job
navigated to the plain Jobs page without opening that job's detail drawer.
Make each linked job deep-link to `/jobs?job=<id>` and have the Jobs page open
the job's detail drawer on mount.

## Current State

- `widgets/companies-page/index.tsx` wired `onOpenJob`, `onNavigateToJob` and
  `onViewAllJobs` all to `navigateToJobs` (a bare `window.location.href =
  '/jobs'`), so the job id was dropped.
- The Jobs page adapter did not read any URL query parameter, so `detailJobId`
  could only be set by clicking a row.

## Implementation Steps

1. `widgets/companies-page/index.tsx`: add `openJob(id)` →
   `/jobs?job=<id>`; wire `onOpenJob` and `onNavigateToJob` to it; keep
   `onViewAllJobs` on the plain `/jobs` navigation.
2. `widgets/jobs-page-v2/index.tsx`: on mount read the `job` search param and
   open the detail drawer for it; clear the `job` param when the drawer closes
   (mirrors the companies page `company` param handling).

## Testing Requirements

- Frontend: `npx vitest run` — 385 passed (48 files).
- `npx tsc --noEmit` — no errors in the changed files.

## Constraints

- Bug fix → SemVer PATCH bump to **3.5.1** in all version locations +
  `check-version.sh`.
