# Prompt 092 - Modern Top-Menu Navigation (replace sidebar)

## Objective

1. Fix a real bug: clicking a sidebar nav item — including the already-active
   one — calls `onClose()` unconditionally, collapsing the sidebar to `w-0` at
   all breakpoints with no desktop reopen control (the hamburger is `lg:hidden`),
   forcing a full page reload.
2. Replace the hand-rolled left sidebar with a single, modern **top header
   menu** (best practice for a ~6-item app), including an `AI` dropdown submenu
   (`LLM Configurations`). Add a mobile hamburger → left sheet nav.
3. Remove the sidebar entirely (`src/widgets/sidebar/`).

## Current State

- `src/widgets/sidebar/index.tsx` — `handleNav` (lines 50–54) calls `onClose()`
  after every `router.push`; aside collapses to `w-0 overflow-hidden` at all
  breakpoints (line 61); reopen button is `lg:hidden` only
  (`src/widgets/main-layout/index.tsx:12–20`).
- `src/widgets/header/index.tsx` — partial top menu (no `AI` item, no submenu).
- Both nav surfaces are hand-rolled `<button>` elements. No shadcn
  `dropdown-menu` wrapper existed (Radix `@radix-ui/react-dropdown-menu` was
  already a dependency).

## Implementation Steps

1. Add shadcn `src/shared/ui/dropdown-menu.tsx` (Root, Trigger, Content, Item,
   Separator) wrapping the existing Radix dependency.
2. Create `src/widgets/header/nav-items.ts` — shared `NAV_ITEMS` config
   (`id`, `label`, `icon`, `color`, optional `children`) including the
   `ai → llm-configurations` submenu.
3. Rewrite `src/widgets/header/index.tsx` — full-width fixed header (`left-0
   right-0`) with brand, top menu (items + `AI` dropdown submenu via
   `DropdownMenu`), theme toggle, generation-history button, and a mobile
   hamburger opening a left `Sheet` with the same items/submenu inline.
4. Rewrite `src/widgets/main-layout/index.tsx` — drop `sidebarOpen` state and
   `<Sidebar>`; keep header + scrollable content (`pt-16`).
5. Delete `src/widgets/sidebar/index.tsx`.
6. Tests — `src/widgets/header/Header.test.tsx`: renders all items, active
   highlight, navigates on non-active click, active click keeps menu visible,
   AI submenu navigates to `/ai/llm-configurations`.
7. Docs — `DESIGN.md` navigation-structure wireframe (top menu), new
   `docs/ux/app-shell.md` (wireframe + states + rules), `docs/ux/README.md`
   index, implementation history.

## Testing Requirements

- Frontend: new `Header.test.tsx` (5 tests); full `npx vitest run`;
  `npm run typecheck` clean for changed files.
- No backend changes.

## Constraints

- No left sidebar; single top-menu nav surface.
- Mobile nav is a sheet, not a second persistent surface.
- Rule 13: wireframe docs updated (`DESIGN.md`, `docs/ux/app-shell.md`).
