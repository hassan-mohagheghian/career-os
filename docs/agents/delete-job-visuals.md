# Agent Note — Diagrams, Charts & Wireframes for the Delete Job Flow

**Status:** For an agent to pick up and run. Read the docs referenced below,
then produce the visuals described here in `docs/` as and when they are needed.

## Context

The Delete Job flow changed to an **optimistic update** so a deleted Job
disappears from the list immediately. The behavior is implemented in:

- `apps/frontend/src/features/jobs-v2/hooks/useJobsInfiniteQuery.ts`
  (`deleteMutation`, optimistic removal + rollback + invalidation)
- `apps/frontend/src/widgets/jobs-page-v2/index.tsx` (`handleDelete`)
- `apps/frontend/src/shared/api/http-client.ts` (`204 No Content` handling)
- `apps/backend/jobs/presentation/api/jobs_v2_router.py` (`DELETE /jobs/{job_id}`)
- `apps/backend/jobs/infrastructure/repositories/sa_job_repository.py`
  (`delete_by_id` hard delete + related rows)

## Artifacts to Produce

Create these in `docs/` (new `docs/agents/` sub-pages or alongside the feature
docs; link them from the relevant README indexes). Prefer Mermaid diagrams so
they render on GitHub. Only produce what is actually needed for the reader to
understand the flow — do not pad.

1. **Sequence diagram of the optimistic delete flow**
   - Actor (User) → JobRow (Delete action) → ConfirmDialog → React Query
     `deleteMutation` → optimistic cache update (remove from pages, decrement
     `total_items`) → `DELETE /api/jobs/{job_id}` → `204` → success toast /
     drawer close → `invalidateQueries` → re-fetch pages.
   - Show the failure path: rollback to snapshot + error toast.
   - Place in `docs/ux/flows/jobs/delete-job.md` (or a new
     `docs/architecture/delete-job-sequence.md`).

2. **State diagram of a Job Row while deleting**
   - States: idle → confirming (dialog open) → deleting (optimistic removal) →
     gone (success) or restored (error).
   - Place in `docs/ux/features/jobs/delete-job.md`.

3. **Wireframe of the destructive confirmation dialog**
   - Title "Delete Job", message *"Permanently delete this job and all its
     processing data?"*, Cancel / Delete (danger) buttons, and the Job Row
     disappearing behind it.
   - ASCII art is acceptable and matches the existing docs style (see the
     current dialog sketch in `docs/ux/features/jobs/delete-job.md`).

4. **Chart of the request/response contract (optional)**
   - A small table or chart showing `DELETE /jobs/{job_id}` → `204` (empty
     body, no JSON parse) versus endpoints returning JSON, reinforcing the
     `204` handling rule.

## Verification

- Mermaid blocks must be valid (use `mermaid` code fences with clear
  labels).
- Existing references in `docs/api/jobs/delete-job.md`,
  `docs/ux/features/jobs/delete-job.md`, and `docs/ux/flows/jobs/delete-job.md`
  must remain correct.
- Update the docs index in `docs/ux/README.md` if a new page is added.
