# Prompt 078 - Company Detail Drawer Single Page + Notes/Links in Edit Drawer

## Objective

Align the Company Detail drawer with the Job Detail drawer:

- **No tabs** — the drawer becomes a single scrollable page.
- Company-exclusive content (intelligence, scores, jobs, notes, links) is
  placed in a single page following the job drawer's ordering, with the
  company-exclusive sections ordered by importance.
- Notes and links become **read-only** in the detail drawer.
- The add/edit notes and links CRUD (`CompanyNotesTab`) moves into the
  Company Edit drawer.

## Current State

- `CompanyDetailDrawer` (`features/companies-v2/components/CompanyDetailDrawer.tsx`)
  renders a tabbed drawer: `Original Notes | Intelligence | Scores | Jobs`.
  The Intelligence tab renders product vs recruiter variants; the Scores tab
  renders the full score breakdown; Jobs tab lists linked jobs.
- `CompanyNotesTab` (notes + links CRUD) is rendered inside the Notes tab.
- `CompanyEditDrawer` (`features/companies-v2/components/CompanyEditDrawer.tsx`)
  edits only core profile fields (name, industry, city, country, website,
  size, type, description).

## Implementation Steps

1. Rewrite `CompanyDetailDrawer.tsx` to a single scrollable page modeled on
   `JobDetailDrawer.tsx`:
   - Header: grade badge + Fit/Success/Overall score cards, company name +
     logo, industry, meta badges, action buttons (View All Jobs, Website,
     Reprocess, Delete).
   - Company Overview / description.
   - Intelligence sections ordered by importance for a visa-seeking engineer:
     Company Overview → Visa & Relocation Signals → Work Environment →
     Engineering Culture → Technology Stack → Growth Opportunities
     (recruiter variant keeps Recruiter Overview → International Hiring →
     Work Environment).
   - Full scores breakdown (grade card, fit/success factors, calculation).
   - Linked Jobs section.
   - Notes (read-only list).
   - Links (read-only list).
2. Remove the `Tabs` import and `activeTab` state.
3. `CompanyNotesTab` (CRUD) moves to `CompanyEditDrawer` below the profile
   fields; detail drawer shows notes/links read-only.
4. Keep product vs recruiter intelligence variants.

## Testing Requirements

- `CompanyNotesTab.test.tsx` still passes (component unchanged, just relocated).
- Frontend suite green: `npx vitest run`.
- `npm run typecheck` adds no new errors beyond the 56 pre-existing baseline.
- Manual: detail drawer shows notes/links but no add/edit controls; edit
  drawer exposes notes/links CRUD.

## Constraints

- No backend changes — this is purely a frontend layout/ownership change.
- Preserve `CompanyDetailDrawer` props used by `CompaniesPage`
  (`companyId`, `onOpenChange`, `onDelete`, `onReprocess`, `onOpenJob`,
  `onNavigateToJob`, `onViewAllJobs`).
- Update `docs/ux/features/companies/company-detail.md` and
  `docs/ux/features/companies/edit-company.md` wireframes to match.

## Follow-up (same session): unify first section, grades, created column

After the single-page refactor, the drawer was further aligned with the Job
Detail drawer and the company processing fix:

1. **Scores after processing were empty** — root cause:
   `build_company_analysis_result` emitted only `fit`/`success`/`overall`
   keys while the v2 API/frontend read `company_fit_score` /
   `company_success_score` / `company_overall_score`. Fixed by emitting
   legacy aliases in `company_analysis_scoring.py` and adding
   `_score_aliases()` normalization in `companies_v2_router.py` so both
   forms are tolerated everywhere.
2. **Grade derived from score** (no dedicated DB/API column): shared
   `gradeForScore` helper in `src/shared/lib/grade.ts`
   (`A++` ≥ 90, `A+` ≥ 80, `A` ≥ 70, `B` ≥ 50, `C` ≥ 30, `D` ≥ 0, `P` = null)
   and shared `GradeBadge` in `src/shared/components/GradeBadge.tsx`
   (`CompanyGradeBadge` re-exports it).
3. **First drawer section unified**: both Job and Company detail drawers now
   start with grade badge + score cards + name/meta. Company header action
   buttons (View All Jobs, Website, Reprocess, Delete) moved to a footer at
   the bottom of the page.
4. **Recommendation prioritized**: both drawers render a Recommendation
   section directly below the score grid (job: recommendation badge + apply
   reason; company: `intelligence.recommendation` priority/observation/
   action/evidence/impact/ideal role/timing).
5. **Grade near scores in lists**: Company list dropped its dedicated Grade
   column — the grade badge now sits inline in the Scores cell
   (`[A+] F 85 S 90 O 88`); Job list added the grade badge to its Scores cell
   too. A Created column was added to the companies table.
6. **`updated_at` on processing**: `sa_company_repository` now bumps
   `updated_at` in `update_fields` / `update_status` / `pick_queued_item`
   (matching `sa_job_repository`), so processing updates the list's Updated
   column.
7. Docs updated: `company-detail.md`, `company-row.md`, `companies/page.md`,
   `jobs/job-row.md`, `jobs/workflow-progress.md`.
8. **Removed legacy `sa_pending_company_repository.py`** — the only remaining
   caller was `generation_repository._query_pending_companies()`, which now
   queries `CompanyModel` directly (mirroring the existing per-company query).
   Deleted the file, its dedicated tests
   (`test_pending_repository.py`, `test_sa_pending_company_repository_extra.py`),
   and the `TestSAPendingCompanyRepository` class in
   `test_sa_repositories.py`. Backend suite: 1210 → 1180 tests, all passing.
