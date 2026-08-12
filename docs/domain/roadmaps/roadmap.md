# Roadmap (bounded context)

## Purpose

This document describes the **Roadmaps** bounded context: a user goal broken into
milestones and tasks, with optional skill links, notes and learning resources. It is
an independent domain entity (spec §5, §7, §28), driven from the Job Application
Workspace as well as a standalone roadmap editor. AI generation of roadmaps (from a
job application) is covered by `docs/ai/roadmap-generation.md`.

## Concepts

| Concept | Entity | Description |
| ------- | ------ | ----------- |
| Roadmap | `Roadmap` | The aggregate root. A personalized goal with a status and source. |
| Goal | `RoadmapGoal` | 1-1 child describing the roadmap's target (job / career / skill / custom). |
| Milestone | `RoadmapMilestone` | A meaningful outcome inside the roadmap (not a mere topic). |
| Task | `RoadmapTask` | A concrete, actionable step inside a milestone. |
| Skill link | `RoadmapSkillLink` | A reference from a milestone/task to a global Skill. |
| Note | `RoadmapNote` | A contextual note attached to a roadmap node. |
| Resource | `RoadmapResource` | A learning resource (article/video/course/...) attached to a node. |

## Sources and Status

`RoadmapSource`: `APPLICATION` (created from a job application), `AI_GENERATED`,
`MANUAL` (default on manual creation).

`RoadmapStatus`: `ACTIVE` (default), `COMPLETED`, `ARCHIVED`.

### Node statuses

| Entity | Statuses |
| ------ | -------- |
| Task | `NOT_STARTED` (default), `IN_PROGRESS`, `COMPLETED`, `SKIPPED` |
| Milestone | `NOT_STARTED` (default), `IN_PROGRESS`, `COMPLETED` |
| Resource | `PLANNED` (default), `IN_PROGRESS`, `COMPLETED` |

Setting a task to `COMPLETED` records `completed_at`; reopening clears it.
`TaskStatus.COMPLETION_STATES` = (`COMPLETED`, `SKIPPED`) — both count toward
progress.

### Goal types and priorities

`GoalType`: `JOB` (used by application/generation roadmaps), `CAREER`, `SKILL`,
`CUSTOM` (default for manual).

`NodePriority` (milestones and tasks): `CRITICAL`, `HIGH`, `MEDIUM` (default), `LOW`.

`ResourceType`: `ARTICLE`, `VIDEO`, `COURSE`, `BOOK`, `DOCUMENTATION`, `PROJECT`,
`OTHER`. `ResourceSource`: `AI`, `USER` (default).

## Aggregate and Cross-Context References

- The `Roadmap` is the aggregate root; it **owns** its goal, milestones, tasks,
  skill links, notes and resources.
- `roadmaps.application_id` and `roadmap_skill_links.skill_id` are **logical
  references** — plain indexed columns, **no FK** into the `application` / `skill`
  schemas (AGENTS.md rule 15). Referential integrity is enforced by the repository /
  application layers; skills are attached via
  `SQLAlchemySkillRepository.resolve_skill` (find-or-create by name/alias/slug).
- FKs exist **only within** the `roadmap` schema (aggregate + children, incl.
  task→milestone, milestone→roadmap).
- Database schema: `roadmap` with tables `roadmaps`, `roadmap_goals`,
  `roadmap_milestones`, `roadmap_tasks`, `roadmap_skill_links`, `roadmap_notes`,
  `roadmap_resources`.

## Business Rules

- A manual roadmap is created with `POST /api/roadmaps` (source `MANUAL`); an
  application-driven roadmap uses `create_from_application` (source `APPLICATION`,
  goal type `JOB`, logical `application_id`).
- Milestones and tasks are ordered by an integer `position`; new children append at
  the end. `PATCH` can reorder via `position`.
- Progress is **computed, not stored**: `compute_progress(roadmap_id)` returns
  `{completed_tasks, total_tasks, overall_percent, milestone_progress}`.
  `overall_percent` = completed-or-skipped tasks / total tasks (0 when no tasks);
  milestone percent = its completed tasks / its tasks.
- Hard delete (rule 9): deleting a roadmap removes its goal, milestones, tasks,
  skill links, notes and resources. Deleting a milestone removes its tasks (and their
  links/notes/resources); deleting a task removes its links/notes/resources.
- Lists default to newest first (`created_at desc`, rule 7); milestones and tasks
  order by `position asc`.

## Domain Events

See `docs/domain/roadmaps/events.md` for the full EDD catalog.

# Related Documents

- `docs/domain/applications/application.md` — the originating application context.
- `implementation-history/144_proposal_roadmap.md` — the spec.
- `implementation-history/145_feature_roadmap_backend_domain.md` — this implementation.