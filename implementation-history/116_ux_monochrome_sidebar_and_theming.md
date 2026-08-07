# Prompt 116 - UX: Monochrome Sidebar + Single-File Theming

## Objective

Six related UI preferences:

1. **Monochrome sidebar**: the sidebar nav previously gave each item its own icon
   color (`text-blue-500`, `text-emerald-500`, `text-violet-500`,
   `text-amber-500`, `text-cyan-500`, `text-rose-500`) and the brand used a
   `primary → purple-500` gradient. Make the whole sidebar monochrome: icons
   inherit the row's text color (active = `text-primary`, idle =
   `text-muted-foreground`), brand mark is solid `bg-primary
   text-primary-foreground`, brand wordmark is `text-primary`.
2. **Theme changeable from one file**: confirm/document that the theme is
   controlled from a single file — `app/globals.css` (`:root` light, `.dark`
   dark, `@theme inline` mapping). Remove the last hard-coded color literal
   (`purple-500`) in the sidebar so no component-level colors block re-theming.
   Note the folder convention: `apps/frontend/app/` is the **Next.js App
   Router** directory and conventionally lives **outside** `src/` (Next.js
   allows either a root `app/` — the default, used here — or `src/app/`), while
   `apps/frontend/src/` holds the FSD layers (`entities/`, `features/`,
   `widgets/`, `shared/`, `app/`). The two `app` folders are unrelated: the root
   one is the Next.js router (`layout.tsx`, `globals.css`, route segments), the
   `src/app/` one is the FSD layer holding only `providers.tsx` (reached via the
   `@/*` → `src/*` alias). Root `app/` takes precedence, so both coexist fine.
3. **Filter dropdowns follow the design**: the toolbar filter dropdowns (Jobs:
   Status / Remote / Visa / Recommendation, Companies: Industry, Skills:
   Category) rendered with the default `SelectTrigger` text color, which did not
   match the app's primary accent used by the **Add Job** button. Make the
   filter dropdown triggers use `text-primary` so the toolbar controls share the
   same accent as the primary CTA buttons (JobsHeader "Add Job", etc.).
4. **Remove dead legacy stylesheets**: `apps/frontend/src/global.css` (a legacy
   theme-token file) and `apps/frontend/src/index.css` (its only importer) are
   **not in use** — the app stylesheet is `app/globals.css`, imported by
   `app/layout.tsx`; no test or config imports them. Delete both files and point
   the shadcn `components.json` `css` field at `app/globals.css` so the single
   theme file story is accurate.
5. **Fix dropdown/select hover consistency**: hovering a filter dropdown item
   (or a `SelectItem` / `DropdownMenuItem` / ghost-outline `Button`) rendered a
   background **and** text tone that looked the same — the legacy compatibility
   bridge in `app/globals.css` (`:root { --accent: var(--primary) }`) is
   unlayered CSS and overrides the semantic `--accent` token from the
   `@layer base` light/dark blocks, so every `bg-accent` hover/focus state
   painted in the strong primary color. Remove that bridge line so `--accent`
   returns to its intended subtle neutral value and hover states are
   background ≠ text again.
6. **Apply the shadcn theme preset** `b4ZVZIPi9h`
   (`npx shadcn@latest apply --preset b4ZVZIPi9h`) — the project's saved
   "radix-lyra" theme (taupe base color, remixicon icons, inverted subtle menu,
   Merriweather heading + JetBrains Mono fonts). The preset re-installs the UI
   components, updates `app/globals.css`, and wires fonts into `app/layout.tsx`.
   Because the preset merges its palette into the project's pre-existing
   **unlayered** `:root`/`.dark` blocks (which override the preset's `@layer
   base` tokens in the cascade), the leftover `@layer base` token block is dead
   code and must be removed so the theme lives in one place.
7. **`./start theme [code]` command**: the dev CLI (`apps/start.py`) gets a
   command that **gets a preset code** — it runs
   `npx shadcn@latest preset decode <code> --json`, decoding the preset from the
   registry and printing its config. The preset code is a **positional
   argument** the user sets, defaulting to `b4ZVZIPi9h` (style `lyra`,
   baseColor `taupe`, chartColor `orange`, iconLibrary `remixicon`, font
   `jetbrains-mono`, fontHeading `merriweather`, radius `none`, menuColor
   `inverted`, menuAccent `subtle`). Read-only: it never applies the theme or
   modifies files.

## Current State

- `apps/frontend/src/widgets/sidebar/nav-items.ts` — `NavItem.color` per item.
- `apps/frontend/src/widgets/sidebar/index.tsx:91` — icons use `item.color`;
  `BrandMark` + 3 wordmark spots use `bg-gradient-to-* from-primary to-purple-500`.
- `apps/frontend/app/globals.css` — the single theme source (Tailwind v4
  `@theme inline` + `:root`/`.dark` tokens); `app/layout.tsx` imports it. Its
  legacy compat bridge sets unlayered `--accent: var(--primary)`, overriding the
  intended `--accent` (light `oklch(0.96 0.002 17.2)` / dark
  `oklch(0.268 0.011 36.5)`) for every `bg-accent` hover/focus consumer
  (`select.tsx`, `dropdown-menu.tsx`, `button.tsx` ghost/outline, `dialog.tsx`).
- After the preset: `app/globals.css` contains the preset's warm-taupe palette
  in the unlayered `:root` (light) + `.dark` blocks, plus the semantic extras
  (`--bg`, `--surface`, `--surface2`, `--green`/`--yellow`/`--blue`/…) the
  project relies on. The preset also emitted a **duplicate** `@layer base`
  `:root`/`.dark` token block (neutral slate) that the unlayered blocks win
  over — dead code to be removed. `app/layout.tsx` now loads Merriweather
  (`--font-heading`) and JetBrains Mono (`--font-mono`) and applies
  `font-mono` on `<html>`; body text stays Inter via the preserved
  `body { font-family: "Inter" }` rule.
- `apps/frontend/src/global.css` + `apps/frontend/src/index.css` — legacy
  stylesheets; `index.css` only imports `global.css`, and nothing else imports
  either (runtime uses `app/globals.css`; vitest `setup.ts` imports neither;
  `src/main.tsx`/`src/App.tsx` no longer exist).
- `apps/frontend/components.json` — `tailwind.css` still points at
  `src/global.css`.
- `apps/frontend/src/features/jobs-v2/components/JobsToolbar.tsx` — 4
  `SelectTrigger` filters with `className="h-7 w-auto text-2xs gap-1"` (default
  text color).
- `apps/frontend/src/features/companies-v2/components/CompaniesToolbar.tsx` and
  `apps/frontend/src/features/skills-v2/components/SkillsToolbar.tsx` — same
  pattern for Industry / Category.
- `docs/ux/app-shell.md` — documents sidebar behavior; no theming section.

## Implementation Steps

1. **`nav-items.ts`**: drop the `color` field from `NavItem` and all items.
2. **`sidebar/index.tsx`**:
   - `NavRow` icon: `w-[18px] h-[18px] shrink-0` only (inherits `currentColor`
     from the row — `text-primary` active, `text-muted-foreground` idle).
   - `BrandMark`: `bg-primary text-primary-foreground` (solid, monochrome).
   - Brand wordmark (desktop rail, mobile top bar, mobile sheet):
     `text-primary`, no gradient.
3. **Filter dropdowns**: add `text-primary` to the toolbar `SelectTrigger`
   className in `JobsToolbar.tsx` (all 4 selects), `CompaniesToolbar.tsx`
   (Industry), and `SkillsToolbar.tsx` (Category) so their text/icon match the
   Add Job button's primary accent.
4. **Remove dead CSS**: delete `apps/frontend/src/global.css` and
   `apps/frontend/src/index.css`; update `apps/frontend/components.json`
   `tailwind.css` → `app/globals.css`.
5. **Fix hover tokens**: delete `--accent: var(--primary);` from the legacy
   compat bridge in `app/globals.css` so the semantic `--accent` token (and
   `--accent-foreground`) come from the `@layer base` blocks; hover/focus on
   `SelectItem`, `DropdownMenuItem`, and ghost/outline `Button` returns to the
   subtle neutral treatment (distinct from the primary-colored text).
6. **Docs** (AGENTS rule 13): update `docs/ux/app-shell.md` — add "Nav icons:
   monochrome" row to the Elements table and a new **Theming** section
   explaining `app/globals.css` is the single-file theme source (and that
   `src/global.css`/`src/index.css` are gone). No wireframe change (layout
   unchanged).
7. **Apply the preset**: run
   `npx shadcn@latest apply --preset b4ZVZIPi9h` (confirm the overwrite prompt)
   from `apps/frontend`. This re-installs the shadcn components under
   `src/shared/ui/` (radix-lyra style), updates `app/globals.css`,
   `components.json`, `package.json` (adds `@remixicon/react`, `radix-ui`,
   `shadcn`), and rewires fonts in `app/layout.tsx`.
8. **Consolidate the theme tokens**: after the preset, delete the dead
   `@layer base :root`/`.dark` token block the preset emitted (the unlayered
   `:root`/`.dark` blocks carry the same tokens and win the cascade), and merge
   the preset's base element rules (`* { border-border outline-ring/50 }`,
   `body { bg-background text-foreground }`, `html { font-mono }`) into the
   single remaining `@layer base` block. Keep the preset's unlayered warm-taupe
   palette as the one source of truth, and keep the project's semantic extras
   (`--bg`, `--surface`, `--green`, …).
 9. **Verify**: `npx vitest run` (all green, 456 before) and `npm run typecheck`
    (no new errors beyond the existing baseline of 43).
10. **Add `./start theme [code]`**: add a `theme(code: str = "b4ZVZIPi9h")`
    command to `apps/start.py` that runs
    `["npx", "shadcn@latest", "preset", "decode", code, "--json"]` with
    `cwd=CLIENT_DIR`, printing the decoded preset code to stdout and logging
    success/failure (exits non-zero on error). The preset code is the positional
    arg the user sets; default `b4ZVZIPi9h`. It is **read-only** — no files are
    written. Verify with `.venv/bin/python apps/start.py theme b4ZVZIPi9h`.

## Testing Requirements

- All existing frontend tests keep passing (456 before this change); the
  sidebar test asserting `text-primary` on the active item must still pass.
- `npm run typecheck` reports only the pre-existing 43 errors (verified present
  before the preset too).
- The preset re-installs UI components — they must keep their existing exports
  (`cn`, `buttonVariants`, …) so callers and the vitest suite keep compiling;
  all 456 tests must pass after the re-install.

## Constraints

- Frontend-only; do not touch the backend.
- No hard-coded Tailwind color literals in the sidebar — everything resolves
  from theme tokens defined in `app/globals.css`.
- Filter dropdown colors use the `text-primary` token (same as the Add Job
  button accent), not new literals.
- Keep `NAV_ITEMS` ids/labels/icons unchanged; only the `color` field goes away.
- Deleting `src/global.css`/`src/index.css` is safe only because nothing
  references them (verified by grep; vitest `setup.ts` and `app/layout.tsx` use
  `app/globals.css`).
- Dropping `--accent: var(--primary)` is safe because no component reads
  `var(--accent)` directly; only shadcn hover/focus utilities consume the
  `accent` tokens, and they want the neutral value.
- AGENTS.md rule 13: docs updated alongside the UI change.
- The preset overwrites `src/shared/ui/*` components — that is intended (they
  move to the radix-lyra style). After applying it, do **not** hand-edit the
  preset's token values; treat the unlayered `:root`/`.dark` blocks in
  `app/globals.css` as the single source of truth and delete the overridden
  `@layer base` duplicates.
- The preset adds fonts (Merriweather heading, JetBrains Mono) and applies
  `font-mono` to `<html>`; body copy intentionally stays Inter (preserved
  `body { font-family: "Inter" }`).
- `./start theme [code]` is **read-only**: it fetches/decodes the preset code
  (given as the positional arg, default `b4ZVZIPi9h`) from the registry and
  prints it (JSON); it never re-installs components, never applies the theme,
  and never writes `app/globals.css` or any other file.
