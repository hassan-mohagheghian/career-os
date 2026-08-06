# List Skills API

## Purpose

Returns a paginated list of Skills for the Skills page.

This endpoint is optimized for browsing, searching, filtering and sorting.

The endpoint is read-only.

It is the cursor-based, paginated variant of `GET /api/skills`. The legacy
`GET /api/skills` endpoint remains available for other consumers; the Skills v2
page uses this endpoint exclusively.

---

# Endpoint

GET /api/skills/list

---

# Query Parameters

## Pagination

| Parameter | Type    | Required | Default |
| --------- | ------- | -------- | ------- |
| page_size | integer | No       | 25      |
| cursor    | string  | No       | —       |

Maximum page_size is 200.

Pagination is **cursor-based** (keyset). The first request omits `cursor`; every
response returns a `next_cursor` (base64-encoded) that is passed as `cursor` for
the next page. When `next_cursor` is `null`, there are no more pages
(`has_more` is false).

---

## Search

| Parameter | Type   |
| --------- | ------ |
| query     | string |

Search is performed against:

- Skill name
- Relevant roles
- Path
- Aliases

Search is case-insensitive (substring match). Empty value is ignored.

---

## Filters

### Category

```text
category=engineering
```

Canonical categories:

- `technical`
- `engineering`
- `professional`
- `domain`
- `career`

Invalid categories return 400.

---

## Sorting

Supported sort fields

```text
created_at

name

level

confidence

market_relevance

mention_count
```

Default: `mention_count` (desc) — highest-demand skills first.

Every sort follows a **NULLS LAST** policy: rows where the sort column is `NULL`
(for example a skill without a confidence score) always sort **after** rows with
a value, in both `asc` and `desc` order.

The cursor is composite (`<value>|<skill_id>`) so pagination can walk the NULL
tail without skipping or duplicating rows.

Order

```text
asc

desc
```

Default: `desc`.

---

# Response

```json
{
  "items": [
    {
      "id": 12,
      "name": "Kubernetes",
      "category": "engineering",
      "level": 4,
      "roles": "DevOps, SRE",
      "path": "./kubernetes/platform",
      "tags": ["infra", "orchestration"],
      "aliases": ["K8s", "Kube"],
      "confidence": 0.85,
      "market_relevance": 0.9,
      "evidence": "...",
      "source_type": "user_input",
      "mention_count": 3,
      "created_at": "..."
    }
  ],
  "has_more": true,
  "next_cursor": "base64..."
}
```

---

# Returned Information

Each row contains only the information required by the Skills page.

Row fields:

| Field              | Description                                           |
| ------------------ | ----------------------------------------------------- |
| `id`               | Skill id.                                             |
| `name`             | Skill name.                                           |
| `category`         | Canonical category.                                   |
| `level`            | Proficiency level (1–10).                             |
| `roles`            | Relevant roles.                                       |
| `path`             | Learning path.                                        |
| `tags`             | Tag list.                                             |
| `aliases`          | Alias list.                                           |
| `confidence`       | AI confidence (0–1) or null.                          |
| `market_relevance` | Market demand (0–1) or null.                          |
| `evidence`         | Evidence string or null.                              |
| `source_type`      | Origin: `user_input` (manual) or `ai_generated` (AI). |
| `mention_count`    | Total job/company mentions referencing this skill.    |
| `created_at`       | Creation timestamp.                                   |

Large objects must never be returned.

Excluded data includes:

- Full roadmap trees
- Generation history
- Raw analysis payloads

Those are loaded by dedicated endpoints
(`GET /api/skill-roadmaps?skill=<name>`, generation history).

---

# Performance Requirements

The endpoint should support:

- Cursor pagination
- Database indexes
- Efficient filtering
- Efficient sorting

The endpoint must not perform N+1 queries.

---

# Errors

400

Invalid query parameters (e.g. unknown category, invalid sort field).

401

Unauthorized.

500

Internal server error.

---

# Related Documents

- docs/ux/features/skills/page.md
- docs/ux/flows/skills/browse-skills.md
- docs/api/api-design.md
