# Prompt 119 - Fix Select dropdowns opening off-screen

## Objective

Fix the Radix `Select` filter dropdowns that open off-screen (menu created
with `data-state="open"` but positioned below the viewport, so nothing is
visible to the user). Affected: the toolbar filters on the Jobs, Companies and
Skills pages and the level/category selects in the skill add/edit drawers.

## Root Cause

Radix Select's default `position="item-aligned"` positions the content by
aligning the selected item with the trigger's value node. The positioning
routine (`SelectItemAlignedPosition.position()` in
`@radix-ui/react-select`) only sets `top`/`left`/`height` when all of
`{trigger, valueNode, contentWrapper, content, viewport, selectedItem,
selectedItemText}` exist. `valueNode` is registered only when `<SelectValue>`
is rendered inside the trigger. The affected selects render custom label
content (e.g. `<Funnel /> <span>Status</span>`) instead of `<SelectValue>`, so
`valueNode` stays null and the routine bails — the portal wrapper keeps only
`position: fixed; z-index: 50` (no `top`/`left`) and the menu lands at the
bottom of the document. DropdownMenus (Generation History, etc.) are unaffected
because they use a different positioning path.

## Implementation Steps

For every `SelectContent` whose trigger does not render `<SelectValue>`, set
`position="popper"` — this switches to `SelectPopperPosition`, which anchors the
content to the trigger with floating-ui and does not require `valueNode`:

- `src/features/jobs-v2/components/JobsToolbar.tsx` — Status, Remote, Visa,
  Recommendation filters (4).
- `src/features/skills-v2/components/SkillsToolbar.tsx` — Category filter (1).
- `src/features/companies-v2/components/CompaniesToolbar.tsx` — Industry
  filter (1).
- `src/features/skills-v2/components/AddSkillDrawer.tsx` — Level, Category (2).
- `src/features/skills-v2/components/SkillEditDrawer.tsx` — Level, Category (2).

Selects that already render `<SelectValue>` (JobEditDrawer, RuleFormDrawer,
GenerationHistoryDrawer) keep item-aligned positioning and are unchanged.

## Testing Requirements

- `npx vitest run` passes (456 tests).
- Headless Chrome (puppeteer-core + system Chrome): opening each affected
  filter renders the listbox inside the viewport below its trigger (previously
  `top: 900px` off-screen); no page errors on `/jobs`, `/companies`, `/skills`.

## Constraints

- No changes to `src/shared/ui/select.tsx` — the component already supports
  popper mode via the `position` prop.
- Behavior/documentation already describes these filters as working; no doc
  drift.
