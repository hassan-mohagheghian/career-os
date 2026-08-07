# Prompt 117 - Apply the theme preset from the CLI

## Objective

Make `./start theme [code]` apply the shadcn preset to the project instead of
only decoding it. The saved theme preset is `b4ZVZIPi9h` (radix-lyra style,
taupe base, remixicon icons, Merriweather heading + JetBrains Mono fonts).

## Current State

`./start theme [code]` runs `npx shadcn@latest preset decode <code> --json` —
read-only, prints the preset config, never applies it. Re-applying the theme
requires the manual command `cd apps/frontend && npx shadcn@latest apply --preset b4ZVZIPi9h`.

## Implementation Steps

1. Update `apps/start.py` `theme` command: replace the `preset decode` call
   with `npx shadcn@latest apply <code> -y` (run with `cwd=CLIENT_DIR`), so the
   preset is actually applied. `-y` skips the interactive confirmation prompt.
   Keep the positional `code` argument defaulting to `b4ZVZIPi9h`, update the
   help text and log messages ("Applying shadcn preset ...").
2. Update `docs/ux/app-shell.md` Theming section: document that
   `./start theme [code]` now applies the preset (`npx shadcn@latest apply`),
   and keep the manual `apply --preset` example as the equivalent one-liner.

## Testing Requirements

- Verify `./start theme` invokes `npx shadcn@latest apply <code> -y` with
  `cwd=apps/frontend`.
- `./start lint` passes (ruff + eslint).

## Constraints

- No file changes other than the theme application performed by the CLI.
- Docs and code stay in sync.
