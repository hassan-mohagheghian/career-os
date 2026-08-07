# Prompt 112 - Feature: Candidate Source Last-Updated Time + Content View

## Objective

After saving a resume or LinkedIn source on the Candidate Profile Import page,
the user previously saw only a toast. Add two pieces of feedback:

1. **Last-updated time**: every saved source shows a relative timestamp
   (`updated_at` or `created_at`) on the Sources-tab SourceCard footers and on
   the Review-tab Connected Sources rows (full local datetime on hover).
2. **View content**: a **View** action on both surfaces opens a read-only dialog
   (`SourceContentDialog`) showing the stored (PII-masked) `raw_text`.

The backend already serializes `raw_text`, `created_at` and `updated_at` in the
`GET /candidates/sources` response — this is a frontend-only change. After an
upload the sources query is invalidated so the new version + timestamp appear
immediately (previously only a toast was shown and the list went stale).

Secondary objective (user directive during implementation):

3. **Analyze Profile progress**: add the shared `ProcessingDrawer` (the same
   queue drawer Jobs / Companies use) to the Candidate page, filtered to
   `target_type="candidate"`, so the user can watch the `CANDIDATE_PROCESSING`
   workflow progress live via SSE. This required extending
   `ProcessingTargetType` with `'candidate'`.

---

# Read Documentation First

Before making changes read:

- docs/ux/features/candidate/profile-import.md
- docs/ux/flows/candidate/import-profile.md
- apps/frontend/src/features/candidate-v2/components/ProfileImportPage.tsx
- apps/frontend/src/entities/candidate/{api.ts, hooks.ts, types.ts, api.test.ts, hooks.test.tsx}
- apps/frontend/src/shared/components/DateTime.tsx
- apps/frontend/src/shared/lib/formatTimeAgo.ts + parseDateTime.ts
- apps/frontend/src/shared/ui/dialog.tsx

---

# Current State

- `ProfileImportPage` uploads via `candidateApi.uploadSource` directly in
  `handleSaveResume` / `handleSaveLinkedin`; success only fires a toast and
  clears the textarea. The `candidate-sources` React Query is NOT invalidated,
  so the Connected Sources list stays stale until a later refetch.
- `CandidateSource` type omits `raw_text` even though the backend returns it.
- `SourceCard` renders only the textarea + save button (no saved-source
  feedback).
- `SourcesCard` (Review tab) rows render `type v{version}` + status badge only
  (no timestamp, no content view).
- Backend: `source_model_to_dict` (`candidates/infrastructure/mappers.py:69`)
  already includes `raw_text`, `created_at`, `updated_at`; `GET
  /candidates/sources` returns full dicts. No backend change needed.

---

# Implementation Steps

1. **`src/entities/candidate/types.ts`**: add `raw_text: string | null` to
   `CandidateSource`.
2. **`src/entities/candidate/hooks.ts`**: add `useUploadSourceMutation` — a
   `useMutation` over `candidateApi.uploadSource({sourceType, rawText})` that
   invalidates `['candidate-sources']` on settle (mirrors
   `useAnalyzeProfileMutation`).
3. **`ProfileImportPage.tsx`**:
   - Use `useUploadSourceMutation` in the handlers (pass onSuccess/onError for
     toasts + textarea clear); derive `savingResume`/`savingLinkedin` from the
     mutation's pending `variables.sourceType`.
   - Add `SourceContentDialog`: `Dialog` + `ScrollArea` + read-only `<pre>` of
     `source.raw_text` (fallback "No content saved.").
   - `SourceCard`: optional `latestSource` + `onView` props; render a footer
     with `Last updated <DateTime format="relative"> · v{n}` and a **View**
     button.
   - `SourcesCard`: add `onView` prop; each row shows relative `DateTime` +
     an icon **View** button (aria-label `View {type} v{n}`).
   - Wire `viewSource` state at page level, pass `latestSourceByType` (newest
     first per type) to both SourceCards and `onView` to SourcesCard.
4. **Tests** (TDD):
   - `hooks.test.tsx`: `useUploadSourceMutation` calls `uploadSource(type, text)`
     and invalidates `['candidate-sources']`.
   - New `ProfileImportPage.test.tsx`: renders "Last updated" footers, opens the
     dialog with content from a SourceCard, Review-tab rows show timestamps +
     per-row View buttons, dialog renders linkedin raw_text.
   - Fix fixtures (`hooks.test.tsx` sources array) to include `raw_text`.
 5. **Docs**: update `profile-import.md` (wireframe, hierarchy, behaviors) and
    `import-profile.md` (steps 1/2/2b, edge case) with ASCII wireframe for the
    footer + dialog; no Mermaid needed beyond existing diagrams (the dialog has
    no new user journey). Keep `DESIGN.md` consistent if it shows the cards.
 6. **Processing progress**: extend `ProcessingTargetType` in the shared
    `ProcessingDrawer` with `'candidate'` (+ candidate empty-state text), add a
    [☑ Processing] button to the Analyze card, render the drawer filtered to
    `target_type="candidate"`, and add a drawer test to `ProfileImportPage.test.tsx`.
 7. **Verify**: `npx vitest run` (all green), `npm run typecheck` (no new errors
    beyond the existing baseline of 49).

---

# Testing Requirements

- All existing frontend tests keep passing (452 before this change).
- New tests assert: relative last-updated renders, View opens dialog with the
  stored `raw_text`, upload invalidates the sources query, Processing button
  opens the candidate queue drawer.
- No backend changes — run `uv run pytest apps/backend/tests/` only as a sanity
  check that nothing regressed (candidate router tests: 12 passing).

---

# Constraints

- Frontend-only change; do not touch the backend.
- Reuse `DateTime`, `Dialog`, `ScrollArea`, `ProcessingDrawer` — do not reinvent
  timestamps/dialogs/progress.
- Timestamps must use the shared `DateTime` component (browser-local, hover
  full datetime) — consistent with the rest of the app.
- Sources arrive newest-first from the repo, so "latest source per type" = first
  matching `source_type` in the list.
- AGENTS.md rule 13: every UI change ships with its wireframe docs.
