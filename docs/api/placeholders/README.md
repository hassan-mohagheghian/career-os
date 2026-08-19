# Placeholders API

## Purpose

The Placeholders API exposes the user's personal-detail values that get injected
into generated resumes and cover letters. It lives in the Placeholders bounded
context router (`/api/placeholders`) — per-context routers (AGENTS.md rule 10).

## Overview

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/placeholders` | List canonical keys (with labels) + any saved values. |
| PUT | `/api/placeholders` | Upsert a flat `{key: value}` map of placeholder values. |

## List placeholders

`GET /api/placeholders`

Returns the canonical `keys` (with human `label`s), the saved `items`, and a flat
`values` map of `{key: value}` for every saved placeholder.

```json
{
  "keys": [
    { "key": "name", "label": "Full name" },
    { "key": "email", "label": "Email" }
  ],
  "items": [
    { "key": "name", "value": "Hassan", "updated_at": null }
  ],
  "values": { "name": "Hassan" }
}
```

## Update placeholders

`PUT /api/placeholders` — body is a flat `{key: value}` map.

Upserts the given values and returns the stored `items`. Empty keys are ignored.

```json
// request
{ "name": "Hassan", "email": "hassan@example.com" }

// response
{
  "items": [
    { "key": "name", "value": "Hassan", "updated_at": "2026-08-19T10:00:00Z" },
    { "key": "email", "value": "hassan@example.com", "updated_at": "2026-08-19T10:00:00Z" }
  ]
}
```

## Related Documents

- `docs/domain/placeholders/placeholders.md` — entity model and business rules.
- `docs/ux/features/placeholders/placeholders.md` — the Placeholders page wireframe.
- `docs/api/API.md` — top-level API overview.