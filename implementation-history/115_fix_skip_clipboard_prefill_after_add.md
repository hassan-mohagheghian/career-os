# Prompt 115 - Fix: Skip Clipboard Prefill on Reopen After Adding an Entity

## Objective

The shared **Create Entity drawer** (Add Job / Add Company) reads the clipboard
and auto-fills the primary URL field **every time it opens**. After a successful
add, the clipboard still holds the just-inserted URL, so the very next open
re-fills the field with the same "already inserted link" — forcing the user to
clear it before adding a different job/company.

Behavior change: when a submission just succeeded, the **next** open of the
drawer must **not** read the clipboard; the URL field opens empty. Prefill
resumes as normal on the open after that (one-shot suppression), so the usual
"copy a URL → open drawer → pre-filled" flow is unaffected when the user has
copied a new link.

Applies to both modes (job and company) since the drawer is shared.

## Current State

- `apps/frontend/src/shared/components/CreateEntityDrawer.tsx:84-98` — a
  `useEffect` on `[open, isCompany]` calls `readClipboardUrl()` on every open and
  prefills `urlInput` (job) or `primaryUrl` (company) when the field is empty.
  The fields are reset on close (`handleOpenChange(false)`), so each reopen
  triggers the prefill with whatever is still in the clipboard.
- `apps/frontend/src/shared/components/CreateEntityDrawer.test.tsx` — clipboard
  prefill tests cover first-open prefill only.
- Docs: `docs/ux/features/jobs/add-job.md` (Clipboard Prefill section) and
  `docs/ux/features/companies/add-company.md` (Primary Link section) state the
  prefill happens "every time the drawer opens".

## Implementation Steps

1. **Test (TDD red)**: in `CreateEntityDrawer.test.tsx`, add a clipboard-prefill
   test that:
   - opens the drawer, waits for the clipboard prefill to fill the URL field;
   - submits (`Add`), closes (`Cancel`), reopens;
   - asserts `readClipboardUrl` was **not** called again and the URL field is
     empty on that reopen;
   - then closes and reopens a second time and asserts the prefill **does** run
     again (one-shot suppression).
2. **Code**: in `CreateEntityDrawer.tsx`, add a `useRef(false)`
   (`skipClipboardPrefill`). In `handleSubmit`, set it to `true` before calling
   `onSubmit`. In the open effect, consume it first: if set, clear it and skip
   the clipboard read entirely.
3. **Docs**: update the Clipboard Prefill paragraphs in
   `docs/ux/features/jobs/add-job.md` and the Primary Link behavior in
   `docs/ux/features/companies/add-company.md` to document the post-add skip.
   No wireframe change (no layout change); keep the existing ASCII wireframes.
4. **Verify**: `npx vitest run` (all green) and `npm run typecheck` (no new
   errors beyond the existing baseline of 49).

## Testing Requirements

- All existing frontend tests keep passing (454 before this change).
- New tests assert the one-shot suppression behavior for the shared drawer.
- `npm run typecheck` reports only the pre-existing 49 errors — none in touched
  files.

## Constraints

- Frontend-only change; do not touch the backend.
- The suppression is **one-shot**: only the immediate next open after a submit
  skips the prefill; subsequent opens keep the clipboard auto-fill.
- Keep the "Tip: a copied link is auto-filled from your clipboard" hint — the
  prefill still exists for normal usage.
- AGENTS.md rule 13: docs updated alongside the UI behavior change (no new
  wireframe needed; the ASCII layouts are unchanged).
