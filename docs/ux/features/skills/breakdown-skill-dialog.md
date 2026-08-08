# Break down Skill Dialog

## Purpose

Modal dialog that splits a composite skill into atomic children. See
`docs/ux/flows/skills/breakdown-skill.md` for the full user journey.

---

# Anatomy

```text
┌──────────────────────────────────────────────┐
│  ✂  Break down <name>                        │
│  Split a composite skill into its atomic     │
│  children. Each child becomes a separate     │
│  skill, this skill's mentions are duplicated │
│  onto every child, and this skill is hidden. │
├──────────────────────────────────────────────┤
│  [ SQL, NoSQL, GraphQL           ]           │
│  ⚠ List at least two atomic skills,          │
│    separated by commas.                      │
├──────────────────────────────────────────────┤
│                    [ Cancel ] [ ✂ Break down ]│
└──────────────────────────────────────────────┘
```

---

# Fields & States

| Part    | Behavior                                                        |
| ------- | --------------------------------------------------------------- |
| Title   | "Break down <skill name>"                                       |
| Input   | Free-text, comma-separated atomic skills; placeholder `e.g. SQL, NoSQL, GraphQL` |
| Error   | Shown when fewer than two distinct names are entered (inline, red) |
| Footer  | `Cancel` closes; `Break down` submits; shows a spinner + "Breaking down..." while pending |

---

# Related Documents

- `docs/ux/flows/skills/breakdown-skill.md`
- `docs/ux/features/skills/skill-row.md`
