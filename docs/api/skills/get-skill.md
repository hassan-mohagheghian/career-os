# Get Skill & Manage Aliases API

## Purpose

Get a single skill (with aliases and tags) and manage its aliases from the
Skill Edit drawer.

---

# Get a skill

## Endpoint

GET /api/skills/{id}

## Response

```json
{
  "id": 12,
  "name": "Kubernetes",
  "level": 4,
  "roles": "DevOps, SRE",
  "path": "./kubernetes/platform",
  "category": "engineering",
  "confidence": 0.85,
  "market_relevance": 0.9,
  "evidence": "...",
  "tags": ["infra"],
  "aliases": ["K8s"],
  "source_type": "user_input",
  "created_at": "..."
}
```

## Errors

| Status | Meaning                        |
| ------ | ------------------------------ |
| 404    | Skill `{id}` not found.        |

---

# Add an alias

## Endpoint

POST /api/skills/{id}/aliases

## Request Body

```json
{ "alias_name": "K8s" }
```

## Response

The updated skill object (`SkillResponse`), including the new `aliases` array.

## Behavior

- Adding an existing alias is idempotent (no duplicate row).
- Empty alias names are rejected.
- Unknown skill returns 404.

---

# Remove an alias

## Endpoint

DELETE /api/skills/{id}/aliases?alias_name={alias_name}

The alias name travels as a **query parameter** (not a path segment) so aliases
containing `/` (e.g. `AI / NLP`) do not break route matching. Callers should URL-
encode the value.

## Response

The updated skill object (`SkillResponse`) with the alias removed.

## Behavior

- Removing a non-existent alias is a no-op.
- Unknown skill returns 404.

---

# Related Documents

- `docs/api/skills/list-skills.md`
- `docs/api/api-design.md`
- `docs/ux/features/skills/edit-skill.md`
