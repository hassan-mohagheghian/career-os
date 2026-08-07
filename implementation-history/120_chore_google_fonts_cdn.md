# Prompt 120 - Load the app fonts from the Google Fonts CDN

## Objective

Load the fonts referenced by the app's styles from the Google Fonts CDN so
they are guaranteed to render even when the `next/font` self-hosted setup is
rebuilt, and keep the CDN import intact across `./start theme` re-applies.

## Current State

The styles reference three families:

- Base/body copy — the preset (`b4ZVZIPi9h`) uses **JetBrains Mono** as the
  base font (`font: jetbrains-mono`); `html` is `@apply font-mono` and the body
  inherits it. A legacy `body { font-family: "Inter", … }` rule in
  `apps/frontend/app/globals.css` overrode this to Inter (see prompt 121).
- `--font-heading` → Merriweather via `next/font/google` in
  `apps/frontend/app/layout.tsx`.
- `--font-mono` → JetBrains Mono via `next/font/google` in the same file.

`./start theme [code]` (`apps/start.py`) runs `npx shadcn@latest apply <code> -y`
which rewrites the `next/font` imports and the `<html>` className in
`app/layout.tsx` (AST-based font handling) and updates the theme tokens in
`app/globals.css`.

## Implementation Steps

1. Add Google Fonts CDN `<link>` tags inside `<body>` in
   `apps/frontend/app/layout.tsx`: preconnect to `fonts.googleapis.com` and
   `fonts.gstatic.com` (crossorigin anonymous) plus the stylesheet for the
   preset's two families — JetBrains Mono (variable 100..800) and Merriweather
   (400/700/900) — with `display=swap`. React 19 hoists these `<link>`
   elements into `<head>`.
2. Keep the existing `next/font/google` setup untouched — it remains the
   build-time mechanism shadcn manages, while the CDN links are the additive
   runtime source that survives re-applying the theme.
3. Document in `docs/ux/app-shell.md` (Theming section) that fonts load from
   the Google Fonts CDN and that the links are preserved by `./start theme`.

## Why this survives `./start theme`

The shadcn apply pipeline edits `app/layout.tsx` only through AST manipulation
of the `next/font/google` import, the font variable statements and the
`<html>` className (see `Qp`/`ld` in the shadcn CLI source). It never touches
`<link>` elements rendered in the body, so the CDN links persist. Verified by
running the same command (`shadcn apply b4ZVZIPi9h -y`) against a copy of the
frontend with the links in place — `layout.tsx` was left byte-for-byte intact.

## Testing Requirements

- `npx tsc --noEmit` shows no new errors in `app/layout.tsx`.
- Re-running the exact theme command the CLI uses preserves the CDN `<link>`
  tags in `app/layout.tsx`.
- `./start lint` passes (ruff + eslint).
