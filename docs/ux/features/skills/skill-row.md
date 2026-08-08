# Skill Row

## Purpose

The Skill Row is a single row in the virtualized Skills list. It renders the
row's columns and inline row actions.

---

# Row Structure

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ ☑ │ Kubernetes [AI] 2 aliases │ engineering │ Lv.4 │ DevOps, SRE │ 90% │ 85% │ 2m │ 3 │ ⋯ │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

# Columns

| Column     | Field                    | Notes                                     |
| ---------- | ------------------------ | ----------------------------------------- |
| Select     | —                        | Checkbox toggling multi-select (hidden unless the Select column is enabled) |
| Name       | `name`                   | Origin badge (AI/Manual) + alias count badge when aliases exist |
| Category   | `category`               | Canonical category badge                  |
| Level      | `level`                  | Rendered as `Lv.{level}`                  |
| Roles      | `roles`                  | Truncated list of relevant roles          |
| Demand     | `market_relevance`       | Percentage or `—` when null               |
| Confidence | `confidence`             | Percentage or `—` when null               |
| Created    | `created_at`             | Relative time via `formatTimeAgo`         |
| Mentions   | `mention_count`          | Sortable count of job/company mentions    |
| Actions    | —                        | Details / Edit / Delete icon buttons      |

---

# Category Badge Colors

| Category    | Color  |
| ----------- | ------ |
| technical   | Blue   |
| engineering | Green  |
| professional| Purple |
| domain      | Orange |
| career      | Cyan   |

---

# Level Display

The level renders as `Lv.{level}` (e.g. `Lv.4`).

---

# Actions

Each row exposes three icon (tooltip) buttons:

| Action  | Icon     | Behavior                                     |
| ------- | -------- | -------------------------------------------- |
| Details | Eye      | Opens the Skill Detail drawer (`?skill=<id>`).|
| Edit    | Pencil   | Opens the Skill Edit drawer.                 |
| Delete  | Trash    | Opens the ConfirmDialog; deletes the skill.  |

All action clicks `stopPropagation` so a click on an action never opens the
Detail drawer. The Select checkbox also stops propagation so selecting a row
never opens the Detail drawer.

---

# Select Column

When the Select column is enabled (toolbar Columns dropdown), each row renders a
leading checkbox:

- Checked state is driven by page-level selection state, not row-local state
  (rows are virtualized/unmounted when scrolled away).
- Clicking the checkbox calls the row's `onToggleSelect(id)` and never triggers
  row navigation.

---

# Demand / Confidence Colors

| Value | Color  |
| ----- | ------ |
| ≥ 80  | Green  |
| ≥ 50  | Yellow |
| < 50  | Orange |
| null  | `—`    |

---

# Origin Badge

The origin badge shows where the skill came from:

| Badge   | `source_type`      | Meaning                                    |
| ------- | ------------------ | ------------------------------------------ |
| AI      | `ai_generated`     | Created by job/company analysis processing |
| Manual  | `user_input`       | Created by the user                        |

The badge is hidden when `source_type` is absent.

---

# Mentions Column

Renders `mention_count` — the total number of job/company analysis mentions
referencing the skill. This is the sum of the skill's own mentions plus the
mentions recorded under any separate skill row whose name matches one of the
skill's aliases (e.g. an ai_generated "K8s" row folds into "Kubernetes" once
"K8s" is registered as an alias). A nonzero count is highlighted; zero renders
muted.

---

# Edge Cases

## Aliases

When `alias_count > 0`, a small badge shows next to the name:

```text
Kubernetes  2 aliases
```

When `alias_count == 0`, no badge is rendered.

## Empty roles / demand / confidence

Empty values render as `—`.

---

# Related Documents

- `docs/ux/features/skills/page.md`
- `docs/ux/features/skills/skill-detail.md`
- `docs/ux/features/skills/edit-skill.md`
