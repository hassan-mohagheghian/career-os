# Prompt 147 - Roadmap Frontend + UX Docs (replaces Application Preparation UI)

## Objective

Frontend for the Roadmap system (MVP, spec `144_feature_roadmap.md` §23–§27, §48)
consuming the backend from prompts 145/146, and **removal of the legacy Application
Preparation UI** which is fully replaced by the roadmap.

UX docs (wireframes + Mermaid) for every new screen must ship in the same change
(AGENTS.md rule 13).

## Current State

- No roadmap code in `apps/frontend/src` (confirmed by search). Legacy preparation
  UI exists:
  - `apps/frontend/src/features/job-application/components/PreparationPlan.tsx`
    (whole file, exported by `features/job-application/index.ts:5`).
  - `ApplicationWorkspace.tsx:19,75,99-109,176-183` — imports `PreparationPlan`,
    `useGeneratePreparationMutation`, renders the "Preparation" section.
  - `entities/application/types.ts:33-61` (`HardSkillRecommendation`,
    `SoftSkillRecommendation`, `ApplicationPreparation`) and `:73` (`preparation` field).
  - `entities/application/api.ts` `generatePreparation` + `hooks.ts:89-97`
    `useGeneratePreparationMutation`.
  - `features/job-application/hooks/useApplicationGeneration.ts` (SSE) +
    `components/GenerationProgress.tsx:12-16` (`artifactLabels.preparation`).
  - Tests: `ApplicationWorkspace.test.tsx`, `GenerationProgress.test.tsx`,
    `entities/application/api.test.ts`.
- Backend (prompts 145/146) provides: `/api/roadmaps` CRUD + milestones/tasks/notes/
  resources/skills, `GET /api/roadmaps/by-application/{application_id}`, and
  `POST /api/applications/{id}/roadmap/generate` → `GenerateResponse(artifact="roadmap")`,
  execution SSE events with `target_type="application"`.
- Frontend conventions: FSD (`entities/`, `features/`, `widgets/`, `shared/`); pages in
  `apps/frontend/app/` (route dirs like `app/skills/page.tsx` → widget). Widget pattern:
  `apps/frontend/src/widgets/skills-page/index.tsx`. UI kit: `shared/ui/*`
  (`Progress`, `Card`, `Button`, `Badge`, `Dialog`, `Collapsible`, `Textarea`, `Select`),
  `shared/components/ConfirmDialog`, `DateTime`, `PageHeader`. Icons: `@phosphor-icons/react`.
- Sidebar nav: `apps/frontend/src/widgets/sidebar/nav-items.ts` (NAV_ITEMS array).
- Docs index: `docs/ux/README.md`; `docs/ux/features/applications/preparation-plan.md`
  and `docs/ux/flows/applications/generate-application-artifacts.md` exist.

## Changes

### A. Remove legacy preparation UI

- Delete `features/job-application/components/PreparationPlan.tsx` and its barrel
  export (`features/job-application/index.ts:5`).
- `ApplicationWorkspace.tsx`: drop `PreparationPlan` import/usage and the
  "Preparation" `ApplicationSection` (176-183); drop `useGeneratePreparationMutation`
  (`:14,:75`) and `handleGeneratePreparation` (`:99-109`). Replace with a **Roadmap**
  section (see C).
- `entities/application/types.ts`: remove `HardSkillRecommendation`,
  `SoftSkillRecommendation`, `ApplicationPreparation`, `preparation` from
  `ApplicationDetail`; `entities/application/api.ts` + `hooks.ts:89-97`: remove
  `generatePreparation` / `useGeneratePreparationMutation`.
- `GenerationProgress.tsx:12-16`: remove the `preparation` label; add `roadmap:
  'Learning roadmap'` (generated artifact now `"roadmap"`).
- Update `ApplicationWorkspace.test.tsx`, `GenerationProgress.test.tsx`,
  `entities/application/api.test.ts`; delete preparation-specific assertions.

### B. Roadmap entity + API client — `apps/frontend/src/entities/roadmap/`

- `types.ts`: `RoadmapStatus`, `RoadmapSource`, `GoalType`, `NodePriority`,
  `TaskStatus`, `MilestoneStatus`, `ResourceType/Status/Source`;
  `RoadmapGoal`, `RoadmapMilestone` (incl. `skills: RoadmapSkillLink[]`, `tasks`,
  progress), `RoadmapTask`, `RoadmapSkillLink`, `RoadmapNote`, `RoadmapResource`,
  `RoadmapSummary` (id, title, goal_type, source, status, progress),
  `RoadmapDetail` (summary + goal + milestones + notes + resources + progress),
  create/update input types.
- `api.ts`: `list()`, `get(id)`, `getByApplication(applicationId)`, `create(input)`,
  `update(id, input)`, `remove(id)`, `addMilestone`, `updateMilestone`,
  `removeMilestone`, `addTask`, `updateTask`, `removeTask`, `addNote`, `removeNote`,
  `addResource`, `updateResource`, `removeResource`, `linkSkill`, `removeSkillLink` —
  all under `/api/roadmaps*` (reuse `@/shared/api` http client; `API_BASE='/api'`).
- `hooks.ts`: react-query hooks mirroring `entities/skill/hooks.ts` patterns
  (query keys prefixed `'roadmap'`, invalidation on mutations).

### C. Application Workspace — Roadmap section

In `ApplicationWorkspace.tsx` replace the Preparation section with a **Roadmap**
section:

- Query `useRoadmapByApplicationQuery(app.id)` (enabled when app exists).
- If no roadmap: empty copy + `Generate roadmap` button →
  `useGenerateRoadmapMutation(app.id)` hitting
  `POST /api/applications/{id}/roadmap/generate`; on success toast + existing
  `useApplicationGeneration` SSE hook (`artifact="roadmap"`) shows
  `GenerationProgress`; on completion invalidate the roadmap query.
- If roadmap exists: card with title, goal, progress bar
  (`shared/ui/progress`), and `View roadmap` → `router.push('/roadmaps/{id}')`
  plus `Regenerate` (re-dispatches generation). Include a delete action
  (rule 9: all cards have a delete button) → `remove(id)` with `ConfirmDialog`.

### D. My Roadmaps page

- Route `apps/frontend/app/roadmaps/page.tsx` → widget
  `apps/frontend/src/widgets/my-roadmaps-page/index.tsx` (`MainLayout` wrapper,
  mirror `widgets/skills-page/index.tsx`).
- Feature `apps/frontend/src/features/roadmaps/components/`:
  - `MyRoadmapsPage.tsx`: `PageHeader` ("My Roadmaps" + `+ New Roadmap`),
    list of `RoadmapCard`s (`Card`: title, goal, source badge, status, progress
    bar, open / edit / delete), empty state.
  - `RoadmapCreateDialog.tsx`: `Dialog` with title, description, goal
    (type select + title + description) → `create(input)` (source=MANUAL).
  - `RoadmapEditDialog.tsx`: edit title/description/goal/status.
  - Reuse `ConfirmDialog` for delete.

### E. Roadmap detail page

- Route `apps/frontend/app/roadmaps/[roadmap_id]/page.tsx` → widget
  `apps/frontend/src/widgets/roadmap-detail-page/index.tsx`.
- Feature `apps/frontend/src/features/roadmaps/components/`:
  - `RoadmapDetailPage.tsx`: back link, goal header (title, description,
    type/goal, target job/company if present), overall `Progress` + counts,
    `[+ Add milestone]`, `[Edit roadmap]`, `[View history →]` placeholder
    (versioning is Phase 2), delete button.
  - `RoadmapMilestoneNode.tsx`: collapsible milestone card
    (`Collapsible`): title, status/priority badges, milestone progress bar,
    expand → task list. Skills chips from `milestone.skills`.
  - `RoadmapTaskRow.tsx`: checkbox/status cycle (NOT_STARTED → IN_PROGRESS →
    COMPLETED/SKIPPED via `updateTask`), title, description, priority badge,
    estimated effort, success criteria, notes/resources count, edit + delete.
  - `TaskEditDialog.tsx` / `MilestoneEditDialog.tsx`: add/edit title,
    description, priority, status, estimated_effort, success_criteria.
  - `NotesSection.tsx` / `ResourcesSection.tsx`: list + add dialog per
    task/milestone (resource: title, url, type, status).
  - `SkillLinkPopover.tsx`: search/link existing skill by name via
    `linkSkill(milestoneId|taskId, skill_name)`.
  - Vertical journey layout matching spec §23–§26 (branching not in MVP; keep
    single vertical path; store positions so reorder works via `updateTask`.
    position`).

### F. Sidebar nav

Add `{ id: 'roadmaps', label: 'Roadmaps', icon: RoadMap }` to
`widgets/sidebar/nav-items.ts` (import `RoadMap` from `@phosphor-icons/react`).

### G. UX docs (rule 13, ASCII wireframes + Mermaid)

- `docs/ux/features/roadmaps/my-roadmaps.md` — list page wireframe
  (`[+ New Roadmap]`, card anatomy, empty state), states, actions.
- `docs/ux/features/roadmaps/roadmap-detail.md` — detail page wireframe: goal
  header, vertical milestone journey, collapsed/expanded milestone nodes
  (spec §24), task row, notes/resources, add/edit/delete, delete button per card.
- `docs/ux/features/roadmaps/roadmap-generation.md` — Application Workspace
  roadmap section states (empty/generating/ready) + generation flow.
- `docs/ux/features/roadmaps/roadmap-create-edit.md` — manual create/edit dialogs.
- `docs/ux/flows/roadmaps/` — `create-manual-roadmap.md`,
  `generate-roadmap-from-application.md` (user journey with states + edge cases,
  Mermaid sequence for generate → SSE → complete → open).
- Update `docs/ux/README.md` index (add roadmaps features + flows; mark
  `preparation-plan.md` and the preparation flow as replaced).
- Update `DESIGN.md` wireframes section (roadmap pages).
- Delete `docs/ux/features/applications/preparation-plan.md` and
  `docs/ux/flows/applications/generate-application-artifacts.md` (or rewrite to
  `roadmap` — coordinate with 146's doc updates).

## Testing Requirements

Frontend (`npx vitest run` in `apps/frontend`):

- `entities/roadmap/api.test.ts` — URL/method mapping for every endpoint.
- `entities/roadmap/hooks` tests — query keys + invalidation.
- `MyRoadmapsPage.test.tsx` — renders cards/empty state, create dialog calls
  `create`, delete confirms then `remove`.
- `RoadmapDetailPage.test.tsx` — renders goal header + milestones + tasks,
  status cycle calls `updateTask`, add milestone/task dialogs, notes/resources,
  skill link.
- `ApplicationWorkspace.test.tsx` (updated) — no Preparation section; roadmap
  generate button dispatches `generateRoadmap`, existing roadmap shows
  `View roadmap` + progress.
- `GenerationProgress.test.tsx` (updated) — `roadmap` label.

Backend untouched in this prompt. Run full frontend suite plus
`npm run lint` and `npm run typecheck`.

## Constraints

- All TypeScript, no JS (rule 3). FSD structure (rule 4).
- Reuse the existing UI kit (`shared/ui/*`, `ConfirmDialog`, `DateTime`,
  `@phosphor-icons/react`) — no new UI framework.
- Every card has a delete button (rule 9); use `ConfirmDialog`.
- All AI generation stays server-side; frontend only dispatches + polls SSE.
- MVP only: no version history, evidence, branching graph, sharing, undo.
- Docs-first (rule 13): wireframes + Mermaid committed with the UI change.