# Skill Categories API

## Purpose

Skill categories form a **dynamic catalog** — the canonical five
(`technical`, `engineering`, `professional`, `domain`, `career`) are seeded by
migration, and users can add their own. A skill belongs to **zero or more**
categories; the legacy `skills.category` column is kept as the denormalized
**primary** category (always equal to `categories[0]`, or `""`).

Assigning a category to a skill auto-creates the catalog row if it does not
exist — there is no separate create step for assignment.

---

# GET /api/skills/categories

Returns the full catalog with per-category aggregates (read-only).

```json
[
  {
    "category": "engineering",
    "count": 42,
    "avg_demand": 0.82,
    "avg_level": 4.3
  },
  {
    "category": "security",
    "count": 7,
    "avg_demand": 0.71,
    "avg_level": 3.9
  }
]
```

| Field       | Description                                                       |
| ----------- | ----------------------------------------------------------------- |
| `category`  | Category name (catalog row, or legacy primary-only value).        |
| `count`     | Visible skills whose effective categories include this category.  |
| `avg_demand`| Average `market_relevance` of those skills, or null.              |
| `avg_level` | Average `level` of those skills, or null.                         |

Rows are sorted by `count` descending, then name. Effective categories include
alias inheritance: a row registered as an alias inherits its canonical skill's
categories (own ∪ canonical), mirroring mention folding.

---

# POST /api/skills/categories

Creates a new catalog category. **Idempotent** — returns the existing row when
the name already exists.

```json
{ "name": "security" }
```

Response (201 on create, 200 on existing):

```json
{ "id": 12, "name": "security", "created": true }
```

- Blank names → `400 Bad Request`.
- Names are trimmed; the unique constraint is case-sensitive.

---

# DELETE /api/skills/categories/{name}

Deletes an **unused** category from the catalog.

```json
{ "status": "deleted", "name": "security" }
```

Errors:

- `404 Not Found` — no catalog row with that name.
- `409 Conflict` — still assigned to skills; body indicates how many:
  `Category "security" is assigned to 3 skill(s) and cannot be deleted`.

---

# Skills payload

Create (`POST /api/skills`) and update (`PUT /api/skills/{id}`) accept an
optional `categories: string[]`. On write the category set replaces the
previous links, the primary `category` is synced to `categories[0]` (or `""`),
and any new names are auto-created in the catalog.

The list/detail responses always include both `category` (primary) and
`categories` (full set). See `docs/api/skills/list-skills.md`.

---

# Related Documents

- `docs/api/skills/list-skills.md`
- `docs/api/skills/get-skill.md`
- `docs/domain/skills/events.md`
- `docs/ux/features/skills/page.md`
