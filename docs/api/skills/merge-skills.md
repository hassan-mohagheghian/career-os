# Merge Skills API

## Purpose

Consolidate duplicate skills into a single canonical skill. Mentions re-point
to the target; the source becomes a hidden alias of the target.

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

`200 OK` with the merged result on success:

```json
{
  "status": "merged",
  "target": { "id": 12, "name": "React", "...": "..." },
  "merged": ["ReactJS"],
  "aliases": ["ReactJS"]
}
```

- `status` — always `"merged"`.
- `target` — the surviving skill (full skill payload).
- `merged` — the names of the source skills that were merged (already hidden).
- `aliases` — the target's full alias list after the merge.

## Behavior

For each source skill:

1. `skill_mentions` rows are re-pointed to the target. Rows whose
   `(source_type, source_id)` key already exists on the target are dropped
   (the target's existing mention is kept).
2. The source name is added as an alias of the target.
3. The source skill is hidden (merged), keeping the alias lineage.

## Errors

| Status | Meaning                                     |
| ------ | ------------------------------------------- |
| 404    | Target or a source skill not found.         |
| 400    | `source_ids` is empty.                      |
| 400    | Target is included in `source_ids`.         |

---

# Related Documents

- `docs/api/skills/get-skill.md`
- `docs/ux/flows/skills/merge-skills.md`
- `docs/ux/features/skills/edit-skill.md`
