# Prompt 135 - Focus search field with the F key

## Objective

Add an `F` keyboard shortcut that focuses the search field on the Jobs,
Companies and Skills list pages, so the user can immediately start typing a new
search from anywhere on the page. The `F` keypress itself is not inserted into
the search box — it only moves focus (and selects any existing query so typing
replaces it).

## Current State

- Each list page has a toolbar with a search input built on the shared
  `DebouncedInput` primitive (`apps/frontend/src/shared/ui/debounced-input.tsx`).
  `DebouncedInput` does not forward a `ref`, so nothing can focus it externally.
- The Jobs page has an `N` shortcut (`useAddJobShortcut`, features/jobs-v2/hooks)
  that opens the Add Job drawer; it is documented in
  `docs/ux/features/jobs/page.md`. Companies and Skills have no shortcuts.
- `docs/ux/features/jobs/page.md` already lists `Ctrl + F → Focus Search`, but no
  `F`-only shortcut is implemented anywhere.

## Changes

- `apps/frontend/src/shared/hooks/useFocusSearchShortcut.ts` (new):
  - `useFocusSearchShortcut(ref, key = 'f')` registers a window `keydown`
    listener. When the key is pressed without modifiers (meta / ctrl / alt /
    shift) and focus is not inside an editable target (INPUT / TEXTAREA /
    SELECT / contenteditable), it prevents the default and focuses + selects the
    input referenced by `ref`.
  - Exported from `apps/frontend/src/shared/hooks/index.ts`.
- `apps/frontend/src/shared/ui/debounced-input.tsx`:
  - Accepts and forwards a `ref` to the underlying `<Input>`.
- `apps/frontend/src/features/jobs-v2/components/JobsToolbar.tsx`,
  `apps/frontend/src/features/companies-v2/components/CompaniesToolbar.tsx`,
  `apps/frontend/src/features/skills-v2/components/SkillsToolbar.tsx`:
  - Create a `useRef<HTMLInputElement>(null)`, pass it to the search
    `DebouncedInput`, and call `useFocusSearchShortcut` with it.
- Tests:
  - `apps/frontend/src/shared/hooks/useFocusSearchShortcut.test.ts` (new).
  - One integration test per toolbar verifying `F` focuses the search input
    (`JobsToolbar.test.tsx`, `CompaniesToolbar.test.tsx`, `SkillsPage.test.tsx`).
- Docs:
  - `docs/ux/features/jobs/page.md`: replace the `Ctrl + F` row with `F`, and
    document the shortcut under Search Behavior.
  - `docs/ux/features/companies/page.md` and
    `docs/ux/features/skills/page.md`: add an `F` shortcut note in the Search /
    Toolbar sections.

## Verification

Frontend:

    cd apps/frontend && npx vitest run   # 524 pass (60 files)
    npx tsc --noEmit                      # no new errors (42 pre-existing unrelated)
    npm run lint

## Constraints

- Match the `useAddJobShortcut` guard pattern (no modifiers, editable-target
  exclusion) and reuse it for all three toolbars via the shared hook.
- No version bump (feature batched at release).
- No behavior change when focus is already inside an editable element.
