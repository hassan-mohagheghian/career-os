# Prompt 124 - Processing Single-Instance Dedup + Drawer UX Fixes

## Objective

Five related fixes:

1. **Processing / reprocess dedup**: retrying or reprocessing a failed item must
   remove it from the Failed section, and each target may have **only one
   active execution** (queued / processing / failed) at a time.
2. **Add Job / Add Company drawer**: every open clears the link input first,
   then reads the clipboard (replacing any stale value).
3. **Rules drawer**: the Save button must use the shared design tokens
   (`variant="default"`), not an ad-hoc `bg-green-500` class.
4. **Navigation**: move Skills one position up (above Candidate).
5. **Drawer headers**: the top-right close button must never overlap header
   action buttons (Edit) — reserve the close-button zone in every drawer that
   renders a right-side header action.

---

# Current State

- `CreateProcessingExecutionUseCase.execute` created executions unconditionally;
  `retry` / `POST /jobs/{id}/process` / `POST /companies/{id}/reprocess` all
  created a new execution while leaving the old FAILED one in the queue's
  Failed section (no dedup, duplicates on double-click).
- `CreateEntityDrawer` clipboard prefill used `prev || url` — a stale URL
  survived a programmatic close and blocked re-prefill.
- `RuleFormDrawer` Save button hard-coded `bg-green-500 hover:bg-green-600`.
- `NAV_ITEMS` order: jobs, companies, candidate, skills, rules, ai.
- `SheetContent` close button is `absolute top-4 right-4` and overlapped the
  right-aligned Edit button in the Job/Company/Skill detail drawers.

---

# Implementation Steps

## 1. Backend — single active execution per target

- `processing/domain/repositories/processing_execution_repository.py` + `sa_processing_execution_repository.py`:
  add `active_execution(target_type, target_id)` returning the most recent
  execution with status in `{queued, starting, running, failed}`.
- `CreateProcessingExecutionUseCase.execute`: raise `ConflictError` when an
  active execution already exists for the target (single creation chokepoint).
- `ExecutionActionService`:
  - extract `_remove_failed(execution)` (mark cancelled + publish
    `queue.entry.removed`), reused by `remove_queue_entry` (failed branch).
  - `retry(execution_id)`: validate FAILED → `_remove_failed` → create + dispatch.
  - new `reprocess(target_type, target_id)`: cancel any active FAILED execution,
    then create (use-case guard 409s on queued/starting/running) + dispatch.
  - helper `_create_and_dispatch`.
- `process_router.process_job` and `root_router.reprocess_company`: delegate to
  `ExecutionActionService.reprocess`. Company status update happens only after
  successful execution creation.

## 2. Backend tests

- `test_execution_actions.py`: retry now cancels the old execution, removes it
  from the queue snapshot; retry of non-failed → 409.
- `test_process_job.py`: process replaces a failed execution; 409 when already
  queued/running; new execution allowed after `completed`.
- `test_root_router_compat.py`: company reprocess replaces a failed execution;
  409 when already active.

## 3. Frontend

- `CreateEntityDrawer.tsx`: on open, clear `urlInput`/`primaryUrl` first, then
  read the clipboard and set the field unconditionally (keep the one-shot
  `skipClipboardPrefill` and the `cancelled` cleanup flag).
- `CreateEntityDrawer.test.tsx`: add a clear-then-read test (stale URL replaced
  on reopen).
- `RuleFormDrawer.tsx`: Save button → `variant="default" size="sm"`, drop the
  `bg-green-500` override.
- `nav-items.ts`: swap `candidate` and `skills`.
- Detail-drawer headers (`JobDetailDrawer`, `CompanyDetailDrawer`,
  `SkillDetailDrawer`): `px-4` → `pl-4 pr-14` so the Edit button clears the
  absolute close button.

## 4. Docs

- `docs/api/processing/retry-processing.md`: retry cancels the failed execution
  (leaves Failed section, kept as cancelled for history); 409 on second active;
  SSE now emits `queue.entry.removed` + `execution.created`.
- `docs/api/processing/process-job.md`: Single Active Execution section.
- `docs/domain/processing/job-state-machine.md`: retry model note.
- `docs/ux/features/jobs/processing-queue.md`: Failed Retry rules + queue rules.
- `docs/ux/features/jobs/add-job.md` + `companies/add-company.md`: clipboard is
  cleared then re-read on every open.
- `docs/ux/features/rules/rule-form-drawer.md`: save button token note.
- `docs/ux/app-shell.md` + `DESIGN.md`: nav order (Skills above Candidate).
- `docs/ux/design-system/drawer.md`: header close-button clearance rule.
- `docs/ux/features/companies/company-detail.md` + `skills/skill-detail.md`:
  header wireframes show Edit left of the corner close button.

---

# Testing Requirements

Backend:

    uv run pytest apps/backend/tests/ -v

Frontend:

    cd apps/frontend && npx vitest run
    npm run lint
    npm run typecheck

---

# Important Constraints

- Application-level dedup only — no DB migration, no partial unique index.
- Retry/reprocess keeps history: the cancelled execution stays in the DB as
  `cancelled` (never hard-deleted).
- The use-case guard is the single chokepoint, so `candidates/analyze` also
  returns 409 if a candidate analysis is already active (consistent with the
  one-instance rule).
- No version bump (chore/bug-fix scope; release only if requested).
