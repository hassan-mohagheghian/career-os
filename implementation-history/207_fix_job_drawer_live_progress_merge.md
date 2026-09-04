# Prompt 207 - Merge Live Step Events into the Job Detail Drawer

## Objective
After prompt 206 (SSE transport verified live end-to-end via curl on both
direct and rewrite-proxy paths), the JobDetailDrawer progress bar still did
not advance during processing in the browser. Make the open drawer's
Processing section update live on every `workflow.step.*` event.

## Current State
- `JobDetailDrawer → ProcessingSection` renders
  `detail.latest_processing_execution.workflow` from the `['job-detail', id]`
  react-query cache (REST snapshot).
- `useProcessingEvents` invalidated `job-detail` only on
  `execution.completed` / `execution.failed`. Step events patched only the
  list caches (status badge), never the detail tree → the drawer's steps and
  progress bars stayed frozen until completion (then one refetch).
- The backend only persists `workflow_progress` at the end of a run, so
  refetching the detail mid-run would regress the UI to the stale tree.

## Implementation Steps
1. `entities/processing/workflowMerge.ts`: new `mergeJobDetailStep`
   (converts `WorkflowStep` → `JobDetailWorkflowStep`, replaces by id
   recursively, recomputes top-level progress).
2. `shared/hooks/useProcessingEvents.ts`:
   - new `patchDetailCache`: on created/started/step events (jobs only),
     patch `['job-detail', id]` status and merge the step into the cached
     workflow tree — no refetch, so no regression.
   - When the cached detail has no tree for the execution (fetched before
     the run), invalidate **once** per execution (`bootstrappedRef`) to
     bootstrap it; terminal events clear the marker.
   - Added missing `workflow.step.completed` / `workflow.step.failed`
     cases (previously fell through silently).
3. Tests in `useProcessingEvents.test.tsx`: merge advances cached progress
   without invalidation; bootstrap refetch happens once for unknown
   executions.
4. No doc changes: `docs/ux/flows/jobs/process-job-live.md` already
   specifies this live behavior; the fix aligns the drawer with it.
   No layout change → no wireframe.

## Testing Requirements
- `npx vitest run src/shared/hooks/useProcessingEvents.test.tsx` (6 tests).
- Full `npx vitest run` before commit.
- Live e2e on terraform stack: reprocess JD, observe SSE
  `started → step.* → completed` timestamps (transport already proven).

## Constraints
- Never refetch `job-detail` on step events (server tree is stale mid-run).
- Company detail has no workflow UI; companies keep list-badge updates only.
- SSE wire contract unchanged.
