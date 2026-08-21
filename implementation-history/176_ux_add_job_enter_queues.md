# Prompt 176 - Add Job drawer: Enter key queues the job

## Objective

In the Import Job drawer, pressing **Enter** in the Job Post URL (or Job Title)
input must add the job **and start processing** — the same action as clicking
"Add & Queue".

## Current State

- `apps/frontend/src/shared/components/CreateEntityDrawer.tsx` renders the Import
  Job (job mode) and Add Company (company mode) drawers. In job mode the footer has
  "Add" (`handleSubmit(false)`, line ~779) and "Add & Queue"
  (`handleSubmit(true)`, line ~792). `handleSubmit(queue)` guards on `canSubmit`
  and `submitting` and calls `onSubmit(buildData(queue))` (line 297).
- The Job Post URL input (line ~414) and Job Title input (line ~441) have no Enter
  handling, so Enter cannot currently submit.
- Related precedent: the "Add Link" URL input already submits on Enter (line 556).

## Changes

- Add a `handleJobEnterKey(e)` handler in `CreateEntityDrawer` that, on `Enter`,
  prevents default and calls `handleSubmit(true)` (add + queue).
- Attach `onKeyDown={handleJobEnterKey}` to the Job Post URL and Job Title inputs
  (job mode only; company mode's "Add & Process" stays disabled/untouched).

## Testing Requirements

- Update `apps/frontend/src/shared/components/CreateEntityDrawer.test.tsx`: a test
  that typing a URL and pressing Enter in the URL input submits with `queue: true`;
  and that Enter with an empty/invalid URL does not submit.
- Run `cd apps/frontend && npx vitest run src/shared/components/CreateEntityDrawer.test.tsx`
  and `npm run typecheck`.

## Constraints

- Respect AGENTS.md rule 13: update `docs/ux/features/jobs/add-job.md` (and the
  flow doc if applicable) to document the Enter shortcut.
- Keep the change minimal and localized to the job drawer inputs; do not alter the
  company drawer, link/note inputs, or the existing buttons.
- Commit this prompt file together with the change.