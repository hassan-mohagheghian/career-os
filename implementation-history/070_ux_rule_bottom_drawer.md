# Prompt 070 - Move Add/Edit Rule Into A Bottom Drawer

## Objective

Move the Add / Edit rule form out of the inline column/row editors in the
Scoring Rules tab and into a drawer that opens from the bottom of the screen
(bottom sheet).

## Current State

`apps/frontend/src/features/rules/components/RulesTab.tsx` renders an inline
form in two places:

- Add: `RuleForm` expands below the "Add rule" button inside each scope column.
- Edit: `RuleForm` replaces the row when the pencil icon is clicked.

The repo already ships a shared bottom-sheet drawer
(`@/shared/components/Drawer`, vaul-based) with a `placement="bottom"` variant,
currently unused.

## Implementation Steps

1. Create `apps/frontend/src/features/rules/components/RuleFormDrawer.tsx`:
   - `Drawer` from `@/shared/components/Drawer` with `placement="bottom"`,
     `variant="full"`.
   - `DrawerHeader` (title "Add Rule" / "Edit Rule", close), `DrawerContent`
     with the existing fields (scope select, category select, key, weight,
     value textarea, description) wrapped in `mx-auto w-full max-w-[560px]`,
     `DrawerFooter` with Cancel + Save (Save disabled until key and value set).
   - Props: `open`, `onOpenChange`, `title`, `initial`, `onSave`.
2. Refactor `RulesTab.tsx`:
   - Remove the inline `RuleForm` rendering and the `editing` / `showAdd`
     column state.
   - Add drawer state `{ open, id, initial }`:
     - "Add rule" opens the drawer with defaults for the column scope (id null).
     - Pencil opens the drawer prefilled with the rule (id = rule.id).
     - Save calls `handleSave(id, form)` for edits or `handleAdd(form)` for new
       rules, then closes the drawer.
   - No API changes.
3. Update `apps/frontend/src/features/rules/components/RulesTab.test.tsx`:
   - Mock `@/shared/components/Drawer` to render children inline when open.
   - Add tests: Add opens the drawer; save calls `onUpdate`; Edit opens
     prefilled with the rule's key/value.

## Testing Requirements

- `cd apps/frontend && npx vitest run` passes (all RulesTab tests).
- `npm run lint` and `npm run typecheck` pass.

## Constraints

- Do not change the rules API contract or request payloads.
- Keep the per-column "Add rule" button and the existing drag/priority/toggle
  row actions intact.
