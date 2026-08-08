# Skill Normalization API (breakdown + promote-to-canonical)

## Purpose

Two normalization operations that keep the skill taxonomy atomic and
case/format-consistent:

- **Break down** a composite skill (e.g. "Data Engineering") into its atomic
  children (e.g. Spark, Airflow).
- **Promote an alias** to be the skill's canonical name.

Both rely on **slug equality** (`skills/domain/slug_utils.py`): names are
matched case/format-insensitively (`NoSQL` ≡ `nosql`, `Data Engineering` ≡
`data engineering`).

---

# Endpoint: POST /api/skills/{id}/breakdown

## Request Body

```json
{
  "child_names": ["Spark", "Airflow"]
}
```

- `child_names` — at least two distinct atomic skill names.

## Response

`200 OK`:

```json
{
  "status": "broken_down",
  "origin": { "id": 12, "name": "Data Engineering", "...": "..." },
  "children": [
    { "id": 13, "name": "Spark" },
    { "id": 14, "name": "Airflow" }
  ],
  "hidden": true
}
```

## Behavior

For each child name:

1. Resolve by exact name → alias → canonical slug (creating a new skill only
   when nothing matches).
2. Record an `origin → child` link in `skill.skill_breakdowns` (idempotent).
3. Duplicate the origin's `skill_mentions` onto the child, deduped by
   `(source_type, source_id)`.

The origin is then soft-hidden (`hidden = 1`). The origin→children map feeds
job analysis extraction so a posting mentioning the composite also surfaces its
children.

## Errors

| Status | Meaning                                              |
| ------ | ---------------------------------------------------- |
| 404    | Origin skill not found.                              |
| 400    | Origin skill is hidden.                              |
| 400    | Fewer than two distinct child names (schema allows `[]` > 1; repo re-checks). |
| 422    | `child_names` fails schema validation (`min_length=2`). |

---

# Endpoint: GET /api/skills/{id}/breakdowns

Returns a skill's children (and origin) after a breakdown:

```json
{
  "children": [{ "id": 13, "name": "Spark" }],
  "origin": { "id": 12, "name": "Data Engineering" }
}
```

`origin` is `null` when the skill is not a breakdown child.

---

# Endpoint: GET /api/skills/breakdowns

Returns the full origin→children map used by extraction:

```json
{
  "breakdowns": [
    {
      "origin": { "id": 12, "name": "Data Engineering" },
      "children": [{ "id": 13, "name": "Spark" }, { "id": 14, "name": "Airflow" }]
    }
  ]
}
```

---

# Endpoint: PATCH /api/skills/{id}/canonical

Promote an alias to be the skill's canonical name; the old canonical name
becomes an alias of the same skill.

## Request Body

```json
{
  "alias_name": "ReactJS"
}
```

## Response

`200 OK` with the full updated skill (name is now `ReactJS`, `React` appears in
`aliases`).

## Errors

| Status | Meaning                                        |
| ------ | ---------------------------------------------- |
| 404    | Skill not found.                               |
| 400    | `alias_name` is not an alias of the skill.     |
| 409    | The alias's slug collides with another skill's canonical slug. |

---

# Slug resolution

Skill and category names normalize to a canonical **slug** (lowercased,
separators collapsed to `-`, punctuation `+ . # -` kept). Equality checks use
the slug so `NoSQL` and `nosql` resolve to the same skill and
`Data Engineering`/`data engineering` to the same category. The slug column is
unique; the one-time `normalize-skills-and-categories` CLI command merges any
pre-existing collisions.

---

# Related Documents

- `docs/api/skills/get-skill.md`
- `docs/api/skills/merge-skills.md`
- `docs/ux/flows/skills/breakdown-skill.md`
- `docs/ux/features/skills/edit-skill.md`
- `docs/domain/skills/events.md`
