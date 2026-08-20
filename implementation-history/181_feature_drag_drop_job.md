# Prompt 181 - Feature: Drag-and-Drop Link Import into the Add Job Drawer

## Objective

Let a user add a job by **dragging a link from another browser tab** into the
Jobs page and dropping it onto either the **Add Job button** or **anywhere on
the Jobs page**. On drop, the Add Job creation drawer opens **pre-filled** with
the dropped URL — nothing is auto-created or auto-queued; the user then presses
**Add** (save only) or **Add & Queue** (save + process) exactly as today. If the
user is not already on the Jobs page, they first navigate there via the Jobs
menu item (the drop surface only exists on the Jobs page).

## Current State

- `JobsHeader.tsx` renders the **Add Job** button (`onClick={onAddJob}`), wired
  through `JobsPage` → widget `jobs-page-v2`.
- The widget's `openAddJob()` reads the clipboard (`readClipboardUrl()`) then
  sets `addJobClipboardUrl` and opens `CreateEntityDrawer` (`mode="job"`), which
  pre-fills the Job Post URL from its `clipboardUrl` prop.
- `CreateEntityDrawer` submits `POST /api/jobs` with a `queue` flag that already
  covers both Add and Add & Queue — **no backend change is needed**.
- There is currently **no drag-and-drop handling** anywhere in the frontend.
- Clipboard helper precedent: `shared/lib/clipboard.ts` (`URL_RE =
  /^https?:\/\/\S+$/i`).

## Implementation Steps

1. **URL extraction helper** (`shared/lib/url-drag.ts`): `isUrlString`,
   `extractUrlFromDataTransfer(dataTransfer)` (first `http(s)` URL from
   `text/uri-list` — skipping `#` comment / blank lines — falling back to
   `text/plain`, validating with the shared regex, else null), and
   `dataTransferHasUrl` (types include `text/uri-list` or `text/plain`).
2. **Add Job button drop target** (`JobsHeader.tsx`): add required prop
   `onAddJobUrl(url: string)`. On the Add Job button add `onDragOver`
   (`preventDefault` + `dropEffect='copy'` when it carries a URL, and highlight
   the button with an emerald ring), `onDragLeave` (clear highlight), and
   `onDrop` (extract URL, `preventDefault` + `stopPropagation`, call
   `onAddJobUrl`). Non-URL drops are ignored.
3. **Page-wide drop surface** (`DropJobOverlay.tsx`): wrapper component that
   shows a "Drop to add job" indicator while a URL drag is over the page
   (drag-enter depth counter) and on drop calls `onDropUrl(url)`. It renders
   children unchanged and the indicator is `pointer-events-none` so it never
   blocks interaction.
4. **Wiring**: `JobsPage` gains `onAddJobUrl(url)` and forwards it to both
   `JobsHeader` instances; the widget adds `openAddJobWithUrl(url)` (sets
   `addJobClipboardUrl` + opens the drawer) and wraps the page in
   `DropJobOverlay onDropUrl={openAddJobWithUrl}`, also passing
   `onAddJobUrl={openAddJobWithUrl}` to `JobsPage`. `stopPropagation` on the
   button prevents double-handling with the overlay.
5. **No auto-queue**: the drawer is only pre-filled; Add / Add & Queue decide
   queueing. No backend change.
6. **Docs + history**: `docs/ux/flows/jobs/drag-drop-job.md` (ASCII wireframe +
   Mermaid: navigate to Jobs → drop on button or page → drawer opens pre-filled
   → Add or Add & Queue), update `docs/ux/README.md` + `DESIGN.md`; this prompt.

## Testing

- `shared/lib/url-drag.test.ts`: uri-list first-URL, comment/blank skip,
  text/plain fallback, rejects non-URLs, null handling, `dataTransferHasUrl`.
- `JobsHeader.test.tsx`: add `onAddJobUrl` to props; drop → called with URL;
  dragover prevents default; non-URL drop ignored.
- `DropJobOverlay.test.tsx`: drag shows hint, drop calls `onDropUrl`, non-URL
  drop ignored.
- Run `npx vitest run` and `npx tsc --noEmit` (existing unrelated pre-existing
  tsc errors in `GenerationProgressCard.test` / `MultiSelect.test` / `skills.ts`
  / `rules-page` are not from this change).

## Constraints

- Drop only **pre-fills** the drawer; never auto-create or auto-queue.
- Only HTTP(S) URLs are accepted; other drops are silently ignored.
- No backend / API changes. No new UI kit components (reuse `Button`, classes).
- Frontend TypeScript only (rule 3); feature-based layout (rule 4).
- One prompt = one commit (with this file).