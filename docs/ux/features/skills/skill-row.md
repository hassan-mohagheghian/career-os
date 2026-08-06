# Skill Row

## Purpose

The Skill Row is a single row in the virtualized Skills list. It renders the
row's columns and inline row actions.

---

# Row Structure

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ Kubernetes 2 aliases │ engineering │ Lv.4 │ DevOps, SRE │ 90% │ 85% │ 2m │ ⋯ │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

# Columns

| Column     | Field                    | Notes                                     |
| ---------- | ------------------------ | ----------------------------------------- |
| Name       | `name`                   | Alias count badge when `alias_count > 0`  |
| Category   | `category`               | Canonical category badge                  |
| Level      | `level`                  | Rendered as `Lv.{level}`                  |
| Roles      | `roles`                  | Truncated list of relevant roles          |
| Demand     | `market_relevance`       | Percentage or `—` when null               |
| Confidence | `confidence`             | Percentage or `—` when null               |
| Created    | `created_at`             | Relative time via `formatTimeAgo`         |
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
Detail drawer.

---

# Demand / Confidence Colors

| Value | Color  |
| ----- | ------ |
| ≥ 80  | Green  |
| ≥ 50  | Yellow |
| < 50  | Orange |
| null  | `—`    |

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
