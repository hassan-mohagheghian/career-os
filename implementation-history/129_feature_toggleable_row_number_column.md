# Prompt 129 - Toggleable Row-Number Column & Row Hover Highlight

## Objective

Add a toggleable **row-number** (`#`) column to all three v2 list pages (Skills,
Jobs, Companies) and give every row a clearly visible **hover/focus highlight**
so the focused row stands out in long virtualized lists.

## Current State

- Skills, Jobs and Companies use virtualized infinite-scroll tables. Skills has
  toggleable Select + Pin columns; Jobs and Companies only toggle Pin. Column
  visibility is managed per-widget state and wired through
  `Page → Toolbar → Table → Row`.
- Grid templates are static string constants per list (`skillsColumns.ts`,
  `jobsColumns.ts`, `companiesColumns.ts`), hand-enumerated per leading-column
  combination (e.g. `SKILL_GRID_TEMPLATE_WITH_PIN_SELECT`).
- Rows highlight on hover with `hover:bg-muted/30`; no focus indication.

## Implementation Steps

1. **Row-number column**
   - Add `showRowNumberColumn` / `onToggleRowNumberColumn` props to
     `SkillsPage`/`SkillsToolbar`/`SkillsTable`/`SkillRow`, the jobs equivalents
     and the companies equivalents.
   - Add `Row number` option to each toolbar's `ColumnsDropdown`.
   - Render the `#` header and a leading 44px cell with
     `rowNumber = virtualItem.index + 1`.
2. **Grid templates → builders**
   - Replace the hand-enumerated template constants with builder functions:
     `buildSkillGridTemplate(showRowNumber, showSelect, showPinned)`,
     `buildJobGridTemplate(showRowNumber, showPinned)`,
     `buildCompanyGridTemplate(showRowNumber, showPinned)`; each prepends
     `44px` per enabled leading column.
3. **Hover/focus highlight** — row class becomes
   `hover:bg-muted/50 hover:ring-1 hover:ring-inset hover:ring-border/60
   focus-within:bg-muted/50` on all three rows.
4. **Widgets** — skills/jobs/companies page adapters own the new state
   (default `false`).
5. **Tests** — row-number render/hide per row, `Row number` toggle per toolbar,
   `#` header + toggle in `SkillsPage.test.tsx`.
6. **Docs** — update `DESIGN.md` and the three `page.md` wireframes + Row Columns
   / toolbar tables (README index notes).

## Testing Requirements

- `cd apps/frontend && npx vitest run`
- `cd apps/frontend && npm run typecheck`

## Constraints

- No behavior change when the row-number column is hidden (default).
- No backend changes.
