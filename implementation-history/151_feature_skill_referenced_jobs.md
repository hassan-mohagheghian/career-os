# Prompt 151 - Referenced Jobs in the Skill Detail Drawer

## Objective

Show a **"Referenced Jobs (n)"** section in the Skill Detail Drawer that lists
the jobs which mention the skill (`skill_mentions` rows with
`source_type="job"`). The `n` equals the number of jobs listed (jobs-only
count — the row-level `mention_count`, which also includes company mentions,
stays unchanged). Clicking a job navigates to `/jobs?job=<id>` (same pattern as
the companies page drawer).

---

# Read Documentation First

- docs/api/API.md
- docs/ux/features/skills/skill-detail.md
- docs/ux/flows/skills/browse-skills.md
- docs/ux/README.md
- docs/ux/DESIGN.md

---

# Current State

- `skill_mentions` stores `{skill_id, source_type, source_id, status, evidence}`
  with `source_type` = `"job"` or `"company"`. `source_id` is the job UUID.
- `SkillDetailDrawer.tsx` shows skill metadata but no jobs.
- The skill list row shows a combined `mention_count` (jobs + companies, alias
  folded) from `GET /api/skills/list`.
- The companies v2 router already composes a cross-context job lookup
  (`companies_v2_router.py` imports `SQLAlchemyJobRepository`), establishing the
  pattern for the skills router to hydrate jobs from `skill_mentions` ids.

---

# Implementation Steps

## 1. Backend: repository access

- `skills/domain/repositories/skill_repository.py`: add abstract method
  `get_job_mention_ids(skill_id: int) -> list[str]` (distinct `source_id`s where
  `source_type == "job"`).
- `skills/infrastructure/repositories/sa_skill_repository.py`: implement it
  against `SkillMentionModel`.

## 2. Backend: schemas

- `skills/presentation/api/schemas/skills.py`: add `SkillJobRefSchema` with
  `{id, title, company, location, fit_score, success_score, overall_score,
  pinned, status, created_at}` and `SkillJobsResponseSchema` with
  `{jobs: [...], total: int}`.

## 3. Backend: endpoint

- `skills/presentation/api/skills_router.py`: add `GET /skills/{id}/jobs`:
  - 404 (`NotFoundError`) when the skill is unknown.
  - `skill_repo.get_job_mention_ids(id)`.
  - Hydrate jobs with `job_repo.search_jobs_cursor(job_ids=..., sort="created_at",
    order="desc")` (inject via `get_job_repo`).
  - Return `SkillJobsResponseSchema`.

## 4. Frontend: data layer

- `entities/skill/types.ts`: `SkillReferencedJob` + `SkillReferencedJobs`.
- `entities/skill/api.ts`: `referencedJobs(skillId) -> GET /skills/{id}/jobs`.
- `entities/skill/hooks.ts`: `useSkillReferencedJobs(skillId)` (`useQuery`,
  `enabled: skillId != null`).

## 5. Frontend: drawer

- `features/skills-v2/components/SkillDetailDrawer.tsx`:
  - New "Referenced Jobs (n)" section (n = listed jobs length).
  - Rows: title/role, company, location, Fit/Success/Overall badges + GradeBadge
    (mirror `CompanyJobsTab` styling).
  - Loading spinner / empty state ("No jobs reference this skill yet.").
  - Clicking a row calls `onOpenJob(id)` (new optional prop).
- `features/skills-v2/components/SkillsPage.tsx`: pass `onOpenJob` to the drawer.
- `widgets/skills-page/index.tsx`: `handleOpenJob = () => window.location.href =
  '/jobs?job=' + encodeURIComponent(id)`.

---

# Testing Requirements

Backend (`apps/backend/tests/skills/`):

- API: skill with job mentions returns those jobs and `total` matches the listed
  length; `source_type="company"` mentions are ignored; unknown skill → 404;
  no mentions → empty list.
- Repo: `get_job_mention_ids` dedupes and only returns job rows.

Frontend (`apps/frontend`):

- `SkillDetailDrawer.test.tsx`: renders job rows when provided; shows n; calls
  `onOpenJob` on click; empty state when none.
- Run `npx vitest run`, `npm run lint`, `npm run typecheck`.

---

# Important Constraints

- Do not change row-level `mention_count` semantics.
- Job count in the drawer is jobs-only and may be lower than `mention_count`
  (which includes companies) — intended.
- List the skill's own job mentions only (no alias-folding in the drawer).
- Follow AGENTS.md: all AI/product logic unchanged; docs updated per rule 13;
  no `print()`; no edits in `entrypoints/api.py`.