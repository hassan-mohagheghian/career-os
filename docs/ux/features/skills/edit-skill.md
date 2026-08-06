# Edit Skill Drawer

## Purpose

The Edit Skill drawer updates the core data of an existing skill via
`PUT /api/skills/{id}`.

---

# Anatomy

```text
┌────────────────────────────────────────────────┐
│ Edit Skill                           ✕        │
├────────────────────────────────────────────────┤
│ Name                                        *  │
│ [Kubernetes ...............................]  │
│                                               │
│ Level                                         │
│ [Lv.4 ▾]                                     │
│                                               │
│ Category                                      │
│ [engineering ▾]                               │
│                                               │
│ Relevant Roles                                │
│ [DevOps, SRE, Platform ...................]   │
│                                               │
│ Tags (comma-separated)                        │
│ [infra, orchestration ....................]   │
│                                               │
│ [Cancel]                          [Save]      │
└────────────────────────────────────────────────┘
```

---

# Fields

| Field          | Type     | Required | Notes                                 |
| -------------- | -------- | -------- | ------------------------------------- |
| Name           | text     | Yes      | Unique skill name.                    |
| Level          | select   | No       | 1–10.                                 |
| Category       | select   | No       | Canonical category.                   |
| Relevant Roles | text     | No       | Comma-separated roles.                |
| Tags           | text     | No       | Comma-separated tags.                 |

---

# Flow

```text
Open row → Edit (or Detail drawer → Edit)
        │
        ▼
Pre-fill with existing values
        │
        ▼
Modify fields
        │
        ▼
Submit (PUT /api/skills/{id})
        │
        ├── Success → toast "Skill updated", close drawer, refresh list
        └── Error   → inline error, drawer stays open
```

---

# Behaviors

- Fields are pre-filled from the existing skill.
- On success the list query is invalidated.
- Cancel closes the drawer without saving.

---

# Related Documents

- `docs/ux/features/skills/page.md`
- `docs/ux/features/skills/skill-detail.md`
- `docs/api/skills/update-skill.md`
