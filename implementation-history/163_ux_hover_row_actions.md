# Prompt 163 - Row Actions on Hover (All Lists)

## Objective
Replace the fixed trailing **Actions** grid column on the Jobs, Companies, and
Skills lists with a **hover-revealed actions overlay** rendered inside the row.
This removes the dedicated Actions column width from the grid template so the
freed space is distributed to the remaining data columns, and declutters each
row by default.

## Current State
- `JobsTable` / `CompaniesTable` / `SkillsTable` each define a `{ label:
  'Actions' }` final `ColumnDef` and render the row actions in the final grid
  cell (right-aligned, `justify-end`).
- The grid templates reserve a fixed trailing column for actions:
  - `jobsColumns.ts` `COLUMN_GRID_TEMPLATE` ends with `130px`.
  - `companiesColumns.ts` `COMPANY_GRID_TEMPLATE` ends with `130px`.
  - `skillsColumns.ts` `SKILL_GRID_TEMPLATE` ends with `110px`.
- The row components (`JobRow`, `CompanyRow`, `SkillRow`) render their `*Actions`
  component inside the last grid cell with `justify-end` and
  `onClick={e => e.stopPropagation()}`.

## Implementation Steps
1. Remove the trailing fixed width from each grid template:
   - `jobsColumns.ts`: drop trailing `130px`.
   - `companiesColumns.ts`: drop trailing `130px`.
   - `skillsColumns.ts`: drop trailing `110px`.
2. Remove the `{ label: 'Actions' }` entry from `COLUMN_DEFS` in `JobsTable`,
   `CompaniesTable`, and `SkillsTable`, and drop the `justify-end` right-align
   logic on the final header cell (it only existed to right-align Actions).
3. In each Row component, make the root element `group relative` and replace the
   final grid actions cell with an absolutely-positioned overlay at the right
   edge of the row that is hidden by default and revealed on hover:
   `absolute inset-y-0 right-1 flex items-center opacity-0 group-hover:opacity-100
   transition-opacity`. Give it a subtle background/ring so it reads over the
   row content (e.g. `bg-card ring-1 ring-border rounded-md shadow-sm px-1`).
   Keep the existing `onClick={e => e.stopPropagation()}` on the overlay so
   action clicks do not trigger row navigation.
4. The loading-skeleton rows in each table map over `visibleColumnDefs`, so they
   shrink automatically once the Actions entry is removed — no change needed.
5. Preserve all existing action semantics (Process/Reprocess/Retry/Cancel/Details
   for jobs; Details/Reprocess/Edit/Delete for companies; Details/Break
   down/Merge/Edit/Delete for skills). Only the presentation/layout changes.

## Testing Requirements
- No existing test asserts on the "Actions" header text or its grid position, so
  existing row/table tests should remain green.
- Add/extend a row test per list asserting the actions are **hidden by default**
  and become **visible on hover** (via the group-hover class), and that an
  action click calls its handler without triggering row navigation.
- Run the frontend suite (`npx vitest run`) and typecheck; all must pass.

## Constraints
- Frontend TypeScript only (`.ts`/`.tsx`), no behavior changes to handlers.
- All three lists (jobs, companies, skills) must be updated consistently.
- AGENTS.md rule 13: update the UX docs (jobs/companies/skills page wireframes
  and `docs/ux/DESIGN.md`) to reflect the hover-revealed actions — remove the
  Actions column from wireframes, note the on-hover toolbar.
