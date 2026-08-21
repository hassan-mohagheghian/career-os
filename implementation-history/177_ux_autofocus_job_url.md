# Prompt 177 - Auto-focus URL input in the Import Job drawer

## Objective

When the Import Job drawer opens, place keyboard focus on the **Job Post URL**
input so the user can immediately type or press Enter (to add & queue, see
Prompt 176) without manually clicking into the field.

## Current State

- `apps/frontend/src/shared/components/CreateEntityDrawer.tsx`: job mode renders
  the Job Post URL input (line ~414); company mode renders the Primary Link input
  (line ~349). Neither is auto-focused when the drawer opens.
- The `Input` component (`src/shared/ui/input.tsx`) forwards all props including
  `autoFocus`.

## Changes

- Add `autoFocus` to the **Job Post URL** input (job mode).
- Add `autoFocus` to the **Primary Link** input (company mode) for consistency.

## Testing Requirements

- Update `apps/frontend/src/shared/components/CreateEntityDrawer.test.tsx`: assert
  the Job Post URL input receives focus when the drawer opens in job mode.
- Run `cd apps/frontend && npx vitest run src/shared/components/CreateEntityDrawer.test.tsx`.

## Constraints

- Respect AGENTS.md rule 13: note the auto-focus in
  `docs/ux/features/jobs/add-job.md` (and `docs/ux/features/companies/add-company.md`).
- Keep the change minimal — do not alter layout, validation, or button behavior.
- Commit this prompt file together with the change.