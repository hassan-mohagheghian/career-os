# Prompt 130 - Candidate Analyze No-Op Feedback

## Objective

Clicking **Analyze Profile** on the Candidate page queues a `CANDIDATE_PROCESSING`
run, but when the latest resume/LinkedIn source versions are already `processed`
the workflow short-circuits (`pending_sources` empty → `MergeNode` no-op) and the
execution completes without creating a new profile version — silently. The user
sees nothing happen and no new entry in Version History.

Fix: when there is nothing new to process, `POST /api/candidates/analyze` returns
an explicit no-op response and does **not** create/dispatch an execution, and the
UI shows an info toast explaining that a new resume/LinkedIn version must be
saved first.

## Current State

- `candidates_router.analyze_profile` always created + dispatched a
  `CANDIDATE_PROCESSING` execution; no-op outcomes were silent.
- `PrepareSourcesNode._known_source_versions` counts only `status == "processed"`
  as known; `MergeNode` returns early when nothing was extracted, so no version
  snapshot is written.
- Frontend `handleAnalyze` always toasts "queued" and switches to Review.

## Implementation Steps

## 1. Backend

- `candidates/domain/repositories/candidate_source_repository.py` +
  `candidates/infrastructure/repositories/sa_candidate_source_repository.py`:
  add `has_unprocessed_sources(profile_id) -> bool` — True when any source row for
  the profile has `status != "processed"` (pending / failed → something to retry).
- `candidates/presentation/api/schemas/candidates.py`:
  `CandidateAnalyzeResponse.execution_id` → `str | None = None`; add
  `reason: str = ""`.
- `candidates/presentation/api/candidates_router.py` `analyze_profile`: inject
  `profile_repo` + `source_repo`; when no current profile or no unprocessed
  sources, return `200 {status: "noop", reason: "no_new_sources"}` via
  `JSONResponse` (decorator stays 202 for the queued path). Otherwise keep the
  existing create + dispatch + `202 {execution_id, status: "queued"}`.

## 2. Backend tests

- `test_candidates_router.py` `TestAnalyze`:
  - `test_dispatches_candidate_processing`: seed a `pending` resume source so the
    dispatch path is still exercised.
  - `test_noop_when_all_sources_processed`: seeded profile + processed source →
    200, `status == "noop"`, `reason == "no_new_sources"`, `execution_id is None`,
    enqueue/publish not called.
  - `test_noop_when_no_profile`: no profile → 200 noop, enqueue not called.

## 3. Frontend

- `entities/candidate/types.ts`: `CandidateAnalyzeResult` →
  `{ execution_id: string | null; status: string; reason?: string }`.
- `features/candidate-v2/components/ProfileImportPage.tsx` `handleAnalyze`: on
  `result.status === "noop"` → `toast.info("No new resume/LinkedIn version to
  process — save a new version first")` and stay on Sources; otherwise the
  existing queued toast + Review switch.
- Tests:
  - `ProfileImportPage.test.tsx`: make the `useAnalyzeProfileMutation` mock invoke
    `onSuccess` with a configurable result; add noop case (info toast + Sources
    tab stays active) and queued case (success toast + Review activated); add
    `info` to the `sonner` mock.
  - `hooks.test.tsx`: add a noop passthrough test for `useAnalyzeProfileMutation`.

## 4. Docs

- `docs/ux/features/candidate/profile-import.md`: analyze behavior row, wireframe
  hint, state diagram (`Noop` branch), component/flow mermaid, empty-state note.
- `docs/ux/flows/candidate/import-profile.md`: Step 3 branches on pending vs noop;
  edge case updated (no sources → no run queued).
- `DESIGN.md`: candidate wireframe note + paragraph under the wireframe.
- This file (`implementation-history/130_...`).

---

# Testing Requirements

Backend:

    uv run pytest apps/backend/tests/candidates/ -v

Frontend:

    cd apps/frontend && npx vitest run
    npm run lint
    npm run typecheck

---

# Important Constraints

- The no-op check is a pre-flight only; the workflow's existing skip logic stays
  as a safety net (no duplicate versions, no wasted LLM calls).
- No DB migration (no schema change).
- No version bump (batched at release, per repo convention).
