# Referenced Jobs for a Skill

## Purpose

List the jobs that mention a skill so the Skill Detail drawer can show which job
postings reference it.

---

# Endpoint

GET /api/skills/{id}/jobs

## Response

```json
{
  "jobs": [
    {
      "id": "019f-...",
      "title": "Platform Engineer",
      "company": "Acme GmbH",
      "location": "Berlin",
      "fit_score": 8,
      "success_score": 7,
      "overall_score": 9,
      "pinned": false,
      "status": "completed",
      "created_at": "2026-08-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

## Behavior

- Only mentions with `source_type="job"` are included; company mentions are
  ignored (the skill row's `mention_count` is broader and also includes
  companies).
- Jobs are returned newest-first (`created_at desc`), with soft-deleted jobs
  excluded.
- A skill with no job mentions returns `{"jobs": [], "total": 0}`.

## Errors

| Status | Meaning                 |
| ------ | ----------------------- |
| 404    | Skill `{id}` not found. |

---

# Related Documents

- `docs/api/skills/list-skills.md`
- `docs/api/api-design.md`
- `docs/ux/features/skills/skill-detail.md`