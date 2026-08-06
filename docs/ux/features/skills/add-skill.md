# Add Skill Drawer

## Purpose

The Add Skill drawer collects the core data for a new skill and creates it via
`POST /api/skills`.

---

# Anatomy

```text
┌────────────────────────────────────────────────┐
│ Add Skill                            ✕         │
├────────────────────────────────────────────────┤
│ Name                                        *  │
│ [......................................]      │
│                                               │
│ Level                                         │
│ [Lv.4 ▾]                                     │
│                                               │
│ Category                                      │
│ [technical ▾]                                 │
│                                               │
│ Relevant Roles                                │
│ [DevOps, SRE, Platform ...................]   │
│                                               │
│ Path                                          │
│ [./kubernetes/platform ...................]   │
│                                               │
│ [Cancel]                          [Add Skill] │
└────────────────────────────────────────────────┘
```

---

# Fields

| Field          | Type     | Required | Notes                                |
| -------------- | -------- | -------- | ------------------------------------ |
| Name           | text     | Yes      | Unique skill name.                   |
| Level          | select   | No       | 1–10, default 4.                     |
| Category       | select   | No       | Canonical category, default technical.|
| Relevant Roles | text     | No       | Comma-separated roles.               |
| Path           | text     | No       | Optional skill path.                 |

---

# Flow

```text
Click "Add Skill"
        │
        ▼
Fill Name (required) + optional fields
        │
        ▼
Submit (POST /api/skills)
        │
        ├── Success → toast "Skill created", close drawer, refresh list
        └── Error   → inline error, drawer stays open
```

---

# Behaviors

- Empty name: submit is disabled / shows validation error.
- On success the list query is invalidated so the new skill appears (sorted
  newest-first by `created_at`).
- The drawer closes automatically on success.
- Cancel closes the drawer without saving.

---

# Related Documents

- `docs/ux/features/skills/page.md`
- `docs/api/skills/create-skill.md`
