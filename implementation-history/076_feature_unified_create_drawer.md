# Prompt 076 - Unified Create Entity Drawer (Job + Company)

## Objective

Replace the two parallel "add" drawers — `AddJobDrawer` (Import Job) and
`AddCompanyDrawer` (Add Company) — with a single shared `CreateEntityDrawer`
component driven by a `mode: 'job' | 'company'` prop.

The shared drawer keeps the existing Job intake form and moves the Company
intake form to a new field order agreed with the user:

```
primary link → optional company name → additional links → optional notes
```

Company mode gets a selectable primary-link title (Website | LinkedIn), and the
Website/LinkedIn title is deactivated in the additional-link selector when it is
already used as the primary title.

The footer mirrors the Job drawer's two-action pattern:

- Company: `[Cancel] [Add] [Add & Process]` — **Add** adds the company to the
  list without processing (`queue: false`); **Add & Process** is rendered but
  **disabled for now**.
- Job: `[Cancel] [Add] [Add & Queue]` — the primary button renamed from
  "Create Job" to "Add" and "Create & Queue" to "Add & Queue" for naming
  consistency.

"Add" never auto-opens the Company Queue drawer (unlike Job "Add & Queue", which
keeps its current queue-drawer-open behavior).

A backend fix is required so the optional company name is actually persisted
(`SQLAlchemyPendingCompanyRepository.create_pending_company` currently drops
`input_text`, `input_type` and `name`), plus a `queue` flag on
`POST /api/pending-companies` so "Add" does not enqueue the entry.

---

# Read Documentation First

Before making changes read:

- docs/ux/features/companies/add-company.md
- docs/ux/features/jobs/add-job.md
- docs/ux/README.md
- DESIGN.md (Add Job Drawer / Add Company Drawer wireframes)
- apps/frontend/src/features/jobs/components/AddJobDrawer.tsx
- apps/frontend/src/features/jobs/components/AddJobForm.tsx
- apps/frontend/src/features/companies-v2/components/AddCompanyDrawer.tsx
- apps/frontend/src/features/jobs/hooks/useCreateJob.ts
- apps/frontend/src/entities/company/api.ts, hooks.ts, types.ts
- apps/backend/shared/presentation/api/root_router.py
- apps/backend/companies/infrastructure/repositories/sa_pending_company_repository.py

---

# Current State

## Frontend

- `features/jobs/components/AddJobDrawer.tsx` (default export, right Sheet
  400px/480px, title "Import Job") wraps `AddJobForm.tsx`; the form collects
  Job Post URL *, optional Job Title, Additional Links (url + title chips),
  Notes (title + content chips) and offers `Create Job` / `Create & Queue`.
- `features/companies-v2/components/AddCompanyDrawer.tsx` (named export)
  embeds `AddCompanyForm` which collects free-text notes, then links, with a
  single `Add & Process` button that posts `{ notes, links, source }` to
  `POST /api/pending-companies`, invalidates the pending + companies queries
  and opens the Company Queue drawer on success.
- `JobsPage` owns the job submit flow via `useCreateJob` and passes
  `onSubmit` / `submitting` / `error` into the drawer; the widgets own the
  drawer open state.
- `CompaniesPage` is presentational: the drawer form does its own API call,
  invalidation and queue-drawer opening.

## Backend

- The real pending-company routes live as compat copies in
  `shared/presentation/api/root_router.py` (the companies-context
  `pending_router.py` is NOT mounted).
- `POST /api/pending-companies` merges `links` into url-notes and calls
  `repo.create_pending_company(...)`, but `create_pending_company` only
  persists `notes` / `source` / `status` — `name`, `input_text` and
  `input_type` are dropped (so the optional company name is lost).

---

# Implementation Steps

## 1. Shared component: `shared/components/CreateEntityDrawer.tsx`

Presentational and mode-driven; no entity/feature imports.

```text
interface CreateEntityDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  mode: 'job' | 'company'
  onSubmit: (data: CreateEntityFormData) => void
  submitting?: boolean
  error?: string | null
}

interface CreateEntityFormData {
  mode: 'job' | 'company'
  job_post_url?: string      // job mode
  job_title?: string         // job mode
  name?: string              // company mode
  primaryLink?: { url: string; title: string }   // company mode
  links: Array<{ url: string; title: string }>
  notes: Array<{ title?: string; content: string }>
  queue: boolean
}
```

- Job mode renders the current `AddJobForm` layout: Job Post URL *, Job Title
  (optional), Additional Links (LinkedIn/Website/Careers/GitHub + custom
  title), Notes (title + content, Requirements/Benefits/Salary/Description
  chips), footer `[Cancel] [Add] [Add & Queue]`. Title "Import Job".
- Company mode renders the new field order: Primary Link * (URL + selectable
  title chips Website | LinkedIn), Company Name (optional), Additional Links
  (4-chip selector; Website/LinkedIn chip disabled when it is the primary
  title), Notes (plain content, no title), footer
  `[Cancel] [Add] [Add & Process]` where **Add & Process is always disabled for
  now** and **Add** submits with `queue: false`. Title "Add Company".
- Submit disabled unless: job mode → valid `http(s)` job post URL; company
  mode → a primary link URL is present.
- Reuse existing UI kit (`Sheet`, `ScrollArea`, `Button`, `Input`,
  `Textarea`) and Phosphor icons.

## 2. Wire into JobsPage

- Replace `AddJobDrawer` import/usage with `CreateEntityDrawer mode="job"`.
- Keep the existing `handleCreateJob` submit flow and the Create & Queue →
  Processing Queue drawer behavior.

## 3. Wire into CompaniesPage + `useCreateCompany` hook

- New `features/companies-v2/hooks/useCreateCompany.ts` wrapping
  `companyApi.pendingCreate` with the same shape as `useCreateJob`
  (`{ createCompany, submitting, error, clearError }`), passing the `queue`
  flag and invalidating `companies-pending` and `companies-v2-infinite` on
  success.
- `CompaniesPage` gains a `handleCreateCompany` that maps the shared payload
  to `{ name, notes, links, source, queue }`, closes the drawer and shows a
  toast. `name` falls back to the primary link URL so the entry has a display
  name.
- Company mode never auto-opens the queue drawer (the `onQueued` → open
  queue-drawer wiring is removed).

## 4. Delete old components

- Remove `features/jobs/components/AddJobDrawer.tsx`,
  `features/jobs/components/AddJobForm.tsx`,
  `features/companies-v2/components/AddCompanyDrawer.tsx` (no other
  consumers exist).

## 5. Backend: persist company name + queue flag

- `SQLAlchemyPendingCompanyRepository.create_pending_company`: accept `name`
  (default `None`) and persist `name`, `input_text`, `input_type` alongside
  `notes` / `source` / `status`. Do NOT write the `links` string column — on
  `CompanyModel` that attribute is shadowed by the `CompanyLinkModel`
  relationship.
- `root_router.create_pending_company` compat handler: pass
  `name=data.get("name")` (or the derived `input_text`) through, and only
  call `enqueue_company_sync(pid)` when `data.get("queue", True)` is truthy.
- `CompanyQueueDrawer` display falls back to `item.name` first so a provided
  company name is visible in the pending queue.

---

# Testing Requirements

Backend (`uv run pytest apps/backend/tests/ -v`):

- Extend `tests/shared/presentation/api/test_root_router_compat.py`: creating
  a pending company with `name` persists the name on the created record; a
  request with `queue: false` does **not** call `enqueue_company_sync`.
- Extend `tests/companies/infrastructure/repositories/test_sa_pending_company_repository_extra.py`:
  `create_pending_company` with a `name` persists it; existing behavior
  (name-less) still returns `name: null`.

Frontend (`cd apps/frontend && npx vitest run`):

- New `shared/components/CreateEntityDrawer.test.tsx`:
  - Job mode renders the job fields and both submit buttons; Add & Queue
    submits `queue: true`; Add submits `queue: false`.
  - Company mode renders primary link → name → additional links → notes order;
    primary title chips are Website | LinkedIn; selecting Website as primary
    disables the Website chip in additional links; Add submits with the
    primary link first and `queue: false`; **Add & Process is always
    disabled**.
  - Submit is disabled without a primary link (company) / valid URL (job).
- Update `JobsPage.test.tsx` mock to `@/shared/components/CreateEntityDrawer`
  (same default-export mock shape).

Docs: update `docs/ux/features/companies/add-company.md`,
`docs/ux/features/jobs/add-job.md`, `docs/ux/README.md` and the `DESIGN.md`
wireframes.

Run frontend `npm run lint` and `npm run typecheck`.

---

# Important Constraints

- One shared component; no duplicated drawer/form implementations.
- All AI calls still go through `LLMService` (unaffected).
- Do not add API routes in `entrypoints/api.py`.
- Do not write to the `links` column on `CompanyModel` (relationship conflict).
- Preserve Job mode behavior exactly; only company behavior/ordering changes.
- No UI change without the wireframe docs update (AGENTS.md rule 13).
