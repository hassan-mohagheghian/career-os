# Prompt 118 - Fix UI kit after applying a different shadcn preset

## Objective

Restore the frontend UI kit after `./start theme bJMTbSfw` applied a
wholesale different shadcn preset over the project's saved theme.

## Current State

Running `./start theme bJMTbSfw` ran `npx shadcn@latest apply bJMTbSfw -y`,
which overwrote the project's saved theme (radix-lyra, taupe base, remixicon
icons, Merriweather heading + JetBrains Mono, rounded-none / text-xs) with a
completely different preset (radix-nova/luma style, stone base, lucide icons,
Inter font, amber palette, rounded-lg / text-sm). Side effects:

- `apps/frontend/app/globals.css` — palette replaced and the `@theme inline`
  block left malformed (`--font-sans: var(--font-sans)}` circular reference,
  `--font-heading` rewired to `--font-sans`).
- `apps/frontend/app/layout.tsx` — Inter font added, `html` switched from
  `font-mono` to `font-sans`.
- `apps/frontend/components.json` — style/baseColor/iconLibrary/menuColor
  changed.
- `apps/frontend/package.json` + `package-lock.json` — `lucide-react` added.
- All 22 `src/shared/ui/*` components re-styled to the nova look (structure /
  Radix primitives unchanged; only classNames and icon imports changed).

The UI components were structurally intact; the breakage was the theme/config
overwrite and the malformed CSS merge.

## Implementation Steps

1. Remove the leftover `apps/frontend/components.json.bak` created by the
   preset tooling.
2. Restore the committed working state (the validated radix-lyra / taupe /
   remixicon theme from `implementation-history/116`):
   `git checkout -- apps/frontend/app apps/frontend/components.json
   apps/frontend/package.json apps/frontend/package-lock.json
   apps/frontend/src/shared/ui`
3. Leave `lucide-react` in `node_modules` (pruned on next `npm install`; no
   longer referenced by `package.json`).

No fresh registry reinstall was performed: the committed components already are
the saved theme, and a registry reinstall would either repeat the overwrite or
pull newer component versions (unnecessary drift).

## Testing Requirements

- `git status` clean for `apps/frontend`.
- Jobs page renders, all 4 select filter triggers present, opening one sets
  `data-state="open"` on the listbox, no page errors (verified headless Chrome).

## Constraints

- Keep the saved theme config (`components.json`) as committed.
- No code/doc drift: docs already describe `b4ZVZIPi9h` as the saved theme.
