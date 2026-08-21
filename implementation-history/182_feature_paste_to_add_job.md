# Prompt 182 - Feature: Paste-to-Add Job (Ctrl/Cmd+V opens the Add Job drawer)

## Objective

Let a user add a job by **copying a job-posting link anywhere** and pressing
**Ctrl+V / Cmd+V on the Jobs page**: the Add Job creation drawer opens
**pre-filled** with the pasted URL. Nothing is auto-created or auto-queued; the
user then presses **Add** (save only) or **Add & Queue** (save + process)
exactly as today. This adds a fourth entry point next to the Add Job button,
the `N` shortcut and drag-and-drop (#181).

## Current State

- Entry points live in the widget adapter `widgets/jobs-page-v2/index.tsx`:
  `openAddJob()` (button click + `N` key via `useAddJobShortcut`) and
  `openAddJobWithUrl(url)` (drag-and-drop via `DropJobOverlay`). Both set
  `addJobClipboardUrl` and flip `addJobDrawerOpen`.
- `CreateEntityDrawer` (`mode="job"`) pre-fills Job Post URL from its
  `clipboardUrl` prop whenever `open` or the prop changes — so setting the URL
  state is sufficient even while the drawer is already open.
- Keyboard conventions are hand-rolled `window.addEventListener('keydown')`
  hooks with a local `isEditableTarget()` guard (`INPUT`/`TEXTAREA`/`SELECT`/
  `contentEditable`) duplicated in `useAddJobShortcut` and
  `useFocusSearchShortcut`.
- There is **no** React `onPaste` handling anywhere in `src/`; "paste" today
  means `navigator.clipboard.readText()` on open (`shared/lib/clipboard.ts`),
  which needs the `clipboard-read` permission. A `paste` **event** delivers the
  payload directly with no permission prompt — the right primitive here.
- URL validation precedent: `isUrlString` in `shared/lib/url-drag.ts`
  (`/^https?:\/\/\S+$/i` on trimmed text).

## Implementation Steps

1. **Hook** `features/jobs-v2/hooks/useAddJobPasteShortcut.ts`: listen for
   `paste` on `window`; ignore events originating from editable targets
   (native paste keeps working in inputs — search box, drawer fields); read
   `clipboardData.getData('text/plain')`, trim, accept only http(s) URLs via
   `isUrlString`; otherwise silently ignore. On match `preventDefault()` and
   call `onPasteUrl(url)`.
2. **Wiring**: in `widgets/jobs-page-v2/index.tsx` mount
   `useAddJobPasteShortcut(openAddJobWithUrl)` next to `useAddJobShortcut` —
   no other component changes.
3. **No auto-queue, no backend change**: the drawer is only pre-filled;
   Add / Add & Queue decide queueing (`POST /api/jobs` `queue` flag unchanged).

## Testing

- `features/jobs-v2/hooks/useAddJobPasteShortcut.test.ts` (vitest +
  `@testing-library/react`, fake `clipboardData` object like
  `DropJobOverlay.test.tsx`): URL paste calls back with the URL and prevents
  default; non-URL text ignored (no callback, default kept); paste inside an
  input ignored (native paste preserved); listener cleaned up on unmount.
- Run `npx vitest run` and `npm run lint` + `npm run typecheck`.

## Constraints

- Paste only **pre-fills** the drawer; never auto-create or auto-queue.
- Only HTTP(S) URLs accepted; other pastes silently ignored (no toast).
- Editable targets keep native paste; no hotkey library; jobs-page scope only
  (mirrors the `N` shortcut).
- Frontend TypeScript only (rule 3); feature-based layout (rule 4).
- Docs: `docs/ux/flows/jobs/paste-to-add-job.md` (ASCII + Mermaid), update
  `docs/ux/features/jobs/add-job.md`, `docs/ux/features/jobs/page.md`,
  `docs/ux/README.md`, `docs/ux/DESIGN.md`; this prompt.
- One prompt = one commit (with this file).
