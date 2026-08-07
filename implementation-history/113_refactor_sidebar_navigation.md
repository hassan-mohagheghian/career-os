# Prompt 113 - Refactor: Modern Left Sidebar Navigation (replace top header menu)

## Objective

Redesign the app shell from the single **top header menu** (introduced in 092)
to a **modern, responsive left sidebar**:

1. Primary navigation moves into a fixed left rail on desktop (`lg+`): brand,
   nav items with icons + labels, active-item accent, inline-expandable `AI`
   submenu, and a collapse toggle that narrows the rail to an icon-only mode.
2. The header's **right-side actions move to the bottom of the sidebar**:
   theme toggle and the Generation History button.
3. On mobile (`<lg`) the rail is hidden; a slim top bar with a hamburger opens
   the sidebar content as a left `Sheet` drawer (same nav, same bottom actions).
4. Page content becomes a `flex` column beside the rail; the old `fixed top-0
   h-12` header and `pt-16` clearance are removed. Page widgets that assumed an
   80px top offset (`h-[calc(100vh-80px)]`) switch to `h-full`.

---

# Read Documentation First

Before making changes read:

- docs/ux/app-shell.md (current top-header spec — will be rewritten)
- DESIGN.md (Navigation Structure section — will be rewritten)
- apps/frontend/src/widgets/header/index.tsx
- apps/frontend/src/widgets/header/nav-items.ts
- apps/frontend/src/widgets/header/Header.test.tsx
- apps/frontend/src/widgets/main-layout/index.tsx
- apps/frontend/src/widgets/{jobs-page-v2,companies-page,skills-page}/index.tsx
- apps/frontend/src/shared/ui/{tooltip,sheet,button}.tsx
- implementation-history/092_feature_top_menu_navigation.md (the change being reversed)

---

# Current State

- `MainLayout` renders `<div class="h-screen overflow-hidden"><main class="flex
  flex-col h-full"><Header/> <div class="flex-1 overflow-y-auto p-4 pt-16">
  <div class="max-w-[1400px] mx-auto">{children}</div></div></main></div>`.
- `Header` is `fixed top-0 h-12`, full-width, and owns: brand, the 6
  `NAV_ITEMS` (Jobs, Companies, Candidate, Skills, Rules, AI→LLM
  Configurations), theme toggle, history button, mobile hamburger + sheet.
- `NAV_ITEMS` lives in `widgets/header/nav-items.ts` (icon + color per item).
- Page widgets (jobs/companies/skills) wrap their content in
  `h-[calc(100vh-80px)]` — the 80px accounts for the 48px header + 32px padding.
- `Header.test.tsx` asserts the `Main navigation` nav role, active `text-primary`
  class, push navigation, and the AI `DropdownMenu` with a `menuitem` sub-item.
- Only `widgets/main-layout` imports `@/widgets/header`.

---

# Implementation Steps

1. **`src/widgets/sidebar/nav-items.ts`**: move `NAV_ITEMS` (+ interfaces)
   from `widgets/header` unchanged — the data is layout-agnostic and reused.
2. **`src/widgets/sidebar/index.tsx`** (new `Sidebar` widget, default export):
   - Desktop rail: `hidden lg:flex flex-col` fixed-width `w-60` (expanded) /
     `w-[68px]` (collapsed), `border-r bg-card`, full height. Brand at top
     (gradient text when expanded, icon-only mark when collapsed).
   - Nav: vertical list of `NAV_ITEMS`; active item gets `bg-primary/10`
     `text-primary` + a left accent bar; collapsed mode shows icon-only rows
     wrapped in `Tooltip` (side `right`) with the label.
   - `AI` renders children inline as an expandable group (chevron rotates,
     `aria-expanded`); on `llm-configurations` route the group + child stay
     highlighted. This replaces the `DropdownMenu`.
   - Bottom cluster (`mt-auto`, top border): collapse toggle button
     (`SidebarSimple` icon, rotates/flips on collapsed), theme toggle (Sun/Moon),
     and Generation History button (List) that opens `GenerationHistoryDrawer`.
   - Mobile: `lg:hidden` slim top bar (`h-12 border-b`) with hamburger button +
     brand; hamburger opens a left `Sheet` (`w-72`) reusing the same nav list and
     bottom cluster; selecting any item closes the sheet.
3. **`src/widgets/main-layout/index.tsx`**: replace the `Header` row with
   `<Sidebar/>`; content becomes `flex-1 overflow-y-auto p-4` (no `pt-16`),
   still wrapped in `max-w-[1400px] mx-auto`. Root stays `h-screen overflow-hidden`.
4. **Page widgets**: change the three `flex flex-col h-[calc(100vh-80px)]`
   containers (jobs-page-v2, companies-page, skills-page) to `h-full`.
5. **Tests** (TDD): rewrite `widgets/header/Header.test.tsx` → move to
   `widgets/sidebar/Sidebar.test.tsx`. Assert: desktop nav role + all 6 labels,
   active tab gets `text-primary`, click navigates + stays visible, AI group
   expands inline and its child navigates to `/ai/llm-configurations`, bottom
   cluster contains theme + history buttons. Delete the old header test file.
6. **Docs** (AGENTS rule 13): rewrite `docs/ux/app-shell.md` for the sidebar
   (ASCII wireframe of the rail + bottom cluster + mobile drawer, plus a Mermaid
   navigation-tree diagram); update `DESIGN.md` Navigation Structure section and
   its ASCII tree; update `docs/ux/README.md` index line for `app-shell.md`.
7. **Verify**: `npx vitest run` (all green), `npm run typecheck` (no new errors
   beyond the existing baseline of 49).

---

# Testing Requirements

- All existing frontend tests keep passing (453 before this change).
- New `Sidebar.test.tsx` covers: all nav items render, active item highlight,
  navigation pushes the right route and the menu stays visible, AI submenu
  expands inline and navigates, and bottom actions (theme + history) render.
- `npm run typecheck` reports only the pre-existing 49 errors — none in touched
  files.

---

# Constraints

- Frontend-only change; do not touch the backend.
- Reuse `NAV_ITEMS`, `Tooltip`, `Sheet`, `Button`, `GenerationHistoryDrawer` —
  do not reinvent nav data or drawers.
- Keep the gradient brand + per-item icon colors; preserve keyboard access and
  ARIA (nav labels, tooltips, `aria-expanded`).
- AGENTS.md rule 13: every UI change ships with its wireframe docs (ASCII +
  Mermaid where a diagram clarifies).
- Delete `widgets/header/` entirely; nothing may still import it.
