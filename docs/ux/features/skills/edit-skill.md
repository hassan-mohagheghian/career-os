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
│ Categories                                    │
│ [engineering ☑ +1 ▾]  (multi-select + add)   │
│                                               │
│ Relevant Roles                                │
│ [DevOps, SRE, Platform ...................]   │
│                                               │
│ Tags (comma-separated)                        │
│ [infra, orchestration ....................]   │
│                                               │
│ Aliases                                       │
│ [K8s] ×  [Kube] ×                             │
│ [Add alias...                    ] [+]       │
│                                               │
│ Make an alias the canonical name              │
│ [Choose alias... ▾]  [♛ Make canonical]       │
│                                               │
│ [⟳ Merge into another skill]                  │
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
| Aliases        | badges + text | No | Add via `+`, remove via `×`.        |
| Make canonical | select + button | No | Promote an alias to the canonical name. |
| Merge          | button   | No       | Opens Merge Skill dialog.             |

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
- **Aliases** — `+` adds via `POST /api/skills/{id}/aliases`; `×` removes via
  `DELETE /api/skills/{id}/aliases?alias_name={name}` (query param, so alias
  names containing `/` like `AI / NLP` work). The alias list refreshes from the
  response and the list query is invalidated.
- **Make canonical** — pick an alias and click **Make canonical**; calls
  `PATCH /api/skills/{id}/canonical`, promoting the alias to the skill's name
  (the old canonical name becomes an alias). The name and alias fields refresh
  from the response.
- **Merge** — opens the Merge Skill dialog; merging calls
  `POST /api/skills/merge` and closes the drawer.
- On success the list query is invalidated.
- Cancel closes the drawer without saving.

---

# Related Documents

- `docs/ux/features/skills/page.md`
- `docs/ux/features/skills/skill-detail.md`
- `docs/ux/flows/skills/merge-skills.md`
- `docs/api/skills/categories.md`
