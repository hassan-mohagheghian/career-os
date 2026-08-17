# Prompt 171 - Add Job Clipboard Prefill Works on First Open

## Objective

Fix a UX bug where adding a new job from a clipboard link forces the user to
open the create-job drawer **twice**: the first open leaves the URL field empty,
and only a second open auto-fills it. The clipboard read must happen **inside the
user gesture** (Add Job button / `n` shortcut) so the `clipboard-read` permission
is granted and the URL prefills on the first open.

## Current State

- The create drawer is opened by `setAddJobDrawerOpen(true)` from the Add Job
  button and the `n` shortcut (`src/widgets/jobs-page-v2/index.tsx:51,184`).
- `CreateEntityDrawer` reads the clipboard in a `useEffect` that runs on `open`
  (`src/shared/components/CreateEntityDrawer.tsx:99-125`), calling
  `readClipboardUrl()` (`src/shared/lib/clipboard.ts`, `navigator.clipboard.readText()`).
- Because the effect runs **after render**, outside any click/keydown gesture,
  `navigator.clipboard.readText()` rejects on the first open (no user activation /
  `clipboard-read` permission), so `readClipboardUrl` returns `null` and the field
  stays empty. The permission is granted by that first attempt, so the second open
  succeeds.
- `CreateEntityDrawer` has a `skipClipboardPrefill` ref that skips prefill on the
  reopen immediately after a successful Add (`:189`, `:109-112`); this forces the
  "must open the drawer twice" behavior after the first add. Because the clipboard
  is now captured fresh in the opening gesture, this suppression is obsolete and
  must be **removed**.

## Changes

### `src/shared/components/CreateEntityDrawer.tsx`

- Add optional prop `clipboardUrl?: string | null` to `CreateEntityDrawerProps`.
- In the open `useEffect`, prefer the gesture-captured `clipboardUrl` when
  non-empty; otherwise fall back to `readClipboardUrl()`. Keep the field-clear.
- **Remove** the `skipClipboardPrefill` ref and its gating in the effect and in
  `handleSubmit`, so the current clipboard prefills on **every** open (including
  the open right after a successful Add). Add `clipboardUrl` to the effect deps.

### `src/widgets/jobs-page-v2/index.tsx`

- Add state `addJobClipboardUrl: string | null`.
- Add `openAddJob` callback that reads the clipboard **in the gesture**:
  `await readClipboardUrl()`, store it in `addJobClipboardUrl`, then open the
  drawer. Use it for the `useAddJobShortcut` handler.
- Pass `openAddJob` and `addJobClipboardUrl` to `JobsPage`.

### `src/features/jobs-v2/components/JobsPage.tsx`

- Add `onOpenAddJob: () => void` and `addJobClipboardUrl: string | null` props.
- Route the header "Add Job" handlers (normal and error states) through
  `onOpenAddJob` instead of directly setting open.
- Pass `clipboardUrl={addJobClipboardUrl}` to `CreateEntityDrawer`.

The company drawer (`CompaniesPage`) keeps the existing effect fallback; it is
unchanged and still falls back to reading the clipboard in the effect.

## Testing

- Frontend: update `CreateEntityDrawer.test.tsx` to assert that a provided
  `clipboardUrl` prop is prefilled on open, that the prefill **repeats** after a
  successful Add (no one-shot skip), and that the fallback read still works; run
  `npx vitest run` and `npm run typecheck`.

## Constraints

- AGENTS.md rule 13: no UI change ships without its wireframe docs under
  `docs/ux/features/`. Update the jobs add-job feature doc to note the gesture-time
  clipboard capture.
- No behavior change for the company drawer.