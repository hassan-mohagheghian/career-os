# Skill Detail Drawer

## Purpose

The Skill Detail drawer shows everything the AI knows about a skill and lets the
user manage its learning roadmap.

---

# Anatomy

```text
┌────────────────────────────────────────────────────────────┐
│ </> Kubernetes (engineering)                       ✕  Edit │
├────────────────────────────────────────────────────────────┤
│ [Details]  [Roadmap]  [History]                           │
│                                                            │
│ ★ Lv.4   Confidence: 85%   Market: 90%                    │
│                                                            │
│ ┌─ Relevant Roles ──────────────────────────────────────┐  │
│ │ DevOps, SRE, Platform                                  │  │
│ └────────────────────────────────────────────────────────┘  │
│ ┌─ Path ─────────────────────────────────────────────────┐  │
│ │ ./kubernetes/platform                                  │  │
│ └────────────────────────────────────────────────────────┘  │
│ ┌─ Tags ─────────────────────────────────────────────────┐  │
│ │ [infra] [orchestration]                                │  │
│ └────────────────────────────────────────────────────────┘  │
│ ┌─ Also Known As ────────────────────────────────────────┐  │
│ │ [K8s] [Kube]                                           │  │
│ └────────────────────────────────────────────────────────┘  │
│ [⚡ Generate Roadmap]                                     │
├────────────────────────────────────────────────────────────┤
│                                          [🗑 Delete]       │
└────────────────────────────────────────────────────────────┘
```

---

# Header

| Element      | Behavior                                         |
| ------------ | ------------------------------------------------ |
| Title        | Skill name + CategoryBadge.                      |
| Edit button  | Switches to the Edit drawer (`onEdit`).          |
| Close        | Closes the drawer, clears `?skill=` param.       |

---

# Tabs

## Details

| Section           | Source field        |
| ----------------- | ------------------- |
| Level             | `level` (Lv.{n})    |
| Confidence        | `confidence` (%)    |
| Market demand     | `market_relevance`  |
| Relevant Roles    | `roles`             |
| Path              | `path`              |
| Tags              | `tags` (badges)     |
| Also Known As     | `aliases` (badges)  |
| Why This Matters  | `evidence`          |
| Generate Roadmap  | Button → `POST /api/skill-roadmaps/generate` |

Sections with no data are omitted (no empty boxes).

## Roadmap

- **Generate** — creates the roadmap (`POST /api/skill-roadmaps/generate`).
- **Extend** — appends branches (`POST /api/skill-roadmaps/extend`), disabled
  until a roadmap exists.
- **Finegrain** — refines detail (`POST /api/skill-roadmaps/finegrain`),
  disabled until a roadmap exists.
- While generating, a compact `GenerationProgressCard` shows live progress.
- The roadmap tree renders recursively (nested `RoadmapNode`); completed nodes
  are checked/struck-through, running nodes show a spinner.
- Empty state: "No roadmap yet. Generate one to see learning path
  recommendations."

## History

- Lists generation history items via the shared `useLocalHistory` hook
  (`context: 'skill'`, filtered by `skill_name`).
- Empty state: "No generation history for this skill."

---

# Footer

| Action | Behavior                                         |
| ------ | ------------------------------------------------ |
| Delete | Opens the ConfirmDialog; deletes the skill,      |
|        | closes drawer, clears `?skill=`.                 |

---

# Behaviors

- Roadmap tree is fetched from `GET /api/skill-roadmaps?skill=<name>` on open.
- After any generate/extend/finegrain action the roadmap refetches and the list
  refreshes (`onRefresh`).
- The `?skill=<id>` URL parameter deep-links the drawer (survives reload).
- Edit swaps the drawer while keeping the same skill selected.

---

# Related Documents

- `docs/ux/features/skills/page.md`
- `docs/ux/features/skills/edit-skill.md`
- `docs/ux/features/skills/skill-row.md`
