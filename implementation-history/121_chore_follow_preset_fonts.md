# Prompt 121 - Make the app fully follow the preset fonts

## Objective

Guarantee the app and every component uses the fonts defined by the shadcn
preset (`b4ZVZIPi9h`: JetBrains Mono base + Merriweather headings) — both
after a fresh `./start theme` re-apply and at rest — by removing the custom
deviations that broke preset compliance.

## Root Cause

The preset `b4ZVZIPi9h` decodes to `font: jetbrains-mono` and
`fontHeading: merriweather`. Its canonical output (verified via a fresh
`shadcn init --preset b4ZVZIPi9h`) sets `html { @apply font-mono }` and defines
only `--font-mono` + `--font-heading` — the entire app renders in JetBrains
Mono, with headings in Merriweather. The app deviated from the preset in three
places:

1. `app/globals.css` had a hardcoded `body { font-family: "Inter", … }` that
   overrode the inherited base font to Inter (which is not a preset font).
2. `font-sans` was undefined in `@theme inline`, so the `font-sans` class used
   by the kbd hints in `features/jobs-v2/components/JobsHeader.tsx` fell back to
   the system font stack instead of the preset base font.
3. The Google Fonts CDN link (added in prompt 120) still loaded Inter.

## Implementation Steps

1. `app/globals.css`: remove the `body { font-family: "Inter", … }` rule so the
   body inherits the preset base font from `html { @apply font-mono }`.
2. `app/globals.css`: add `--font-sans: var(--font-mono)` to the `@theme inline`
   block so any `font-sans` usage resolves to the preset base font (JetBrains
   Mono) instead of the system stack. This declaration is additive and survives
   `./start theme` (the apply pipeline only adds missing theme tokens, never
   removes existing ones).
3. `app/layout.tsx`: drop Inter from the Google Fonts CDN stylesheet URL —
   only JetBrains Mono and Merriweather are preset fonts.
4. Update `docs/ux/app-shell.md` (Theming/fonts section) and prompt 120 to
   reflect that the base font is JetBrains Mono (the earlier "body copy stays
   Inter" note was incorrect).

## How this stays consistent with `./start theme`

Re-applying the preset regenerates the same `--font-mono`/`--font-heading`
tokens and the `next/font` JetBrains Mono + Merriweather setup, and preserves
the CDN `<link>` tags and the additive `--font-sans` mapping — so the app is
preset-faithful both before and after a theme re-apply.

## Testing Requirements

- `npx tsc --noEmit` shows no new errors in `app/layout.tsx`.
- `app/globals.css` contains no `Inter` reference; the CDN URL loads only the
  preset families.
- `grep -rn font-sans apps/frontend/src` still resolves via `--font-sans`
  (no component forces the system stack).
- `./start lint` passes (ruff + eslint).
