# Skill Detail Drawer

## Purpose

The Skill Detail drawer shows everything the AI knows about a skill.

---

# Anatomy

```text
┌────────────────────────────────────────────────────────────┐
│ </> Kubernetes (engineering) [AI]                 ✕  Edit │
├────────────────────────────────────────────────────────────┤
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
│ ┌─ Why This Skill Matters ───────────────────────────────┐  │
│ │ Critical for cloud-native platform engineering.         │  │
│ └────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────┤
│                                          [🗑 Delete]       │
└────────────────────────────────────────────────────────────┘
```

---

# Header

| Element      | Behavior                                         |
| ------------ | ------------------------------------------------ |
| Title        | Skill name + CategoryBadge + OriginBadge.        |
| Edit button  | Switches to the Edit drawer (`onEdit`).          |
| Close        | Closes the drawer, clears `?skill=` param.       |

---

# Content

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

Sections with no data are omitted (no empty boxes).

---

# Footer

| Action | Behavior                                         |
| ------ | ------------------------------------------------ |
| Delete | Opens the ConfirmDialog; deletes the skill,      |
|        | closes drawer, clears `?skill=`.                 |

---

# Behaviors

- The `?skill=<id>` URL parameter deep-links the drawer (survives reload).
- Edit swaps the drawer while keeping the same skill selected.

---

# Related Documents

- `docs/ux/features/skills/page.md`
- `docs/ux/features/skills/edit-skill.md`
- `docs/ux/features/skills/skill-row.md`
