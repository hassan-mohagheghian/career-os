# Merge Skills API

## Purpose

Consolidate duplicate skills into a single canonical skill. Mentions, roadmap
references, and progress re-point to the target; the source becomes a hidden
alias of the target.

---

# Endpoint

POST /api/skills/merge

## Request Body

```json
{
  "target_id": 12,
  "source_ids": [13]
}
```

- `target_id` — the skill that survives the merge.
- `source_ids` — one or more skills to merge into the target.

## Response

`204 No Content` on success.

## Behavior

For each source skill:

1. `skill_mentions` rows are re-pointed to the target. Rows whose
   `(source_type, source_id)` key already exists on the target are dropped
   (the target's existing mention is kept).
2. Roadmap references and progress/job rows are re-pointed to the target.
3. The source name is added as an alias of the target.
4. The source skill is hidden (merged), keeping the alias lineage.

## Errors

| Status | Meaning                                     |
| ------ | ------------------------------------------- |
| 404    | Target or a source skill not found.         |
| 400    | `source_ids` is empty or target ∈ source_ids. |

---

# Related Documents

- `docs/api/skills/get-skill.md`
- `docs/ux/flows/skills/merge-skills.md`
- `docs/ux/features/skills/edit-skill.md`
