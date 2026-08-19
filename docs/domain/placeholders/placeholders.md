# Placeholders (bounded context)

## Purpose

This document describes the **Placeholders** bounded context: a small catalog of
user-supplied personal details (`{{token}}`) that are injected into generated job
application documents (tailored resumes and cover letters) when they are served,
copied, or exported to PDF.

The Placeholders context is an **independent domain entity** — it owns the values
so the Job Application Workspace (a different bounded context) can substitute them
**without a cross-context FK** (AGENTS.md rule 15).

## Concepts

| Concept | Entity | Description |
| ------- | ------ | ----------- |
| Placeholder | `Placeholder` | A single named, user-supplied value (`key`, `value`). |
| Placeholder key | `PlaceholderKey` | Canonical token catalog the page edits and documents reference. |

### Canonical keys

`PlaceholderKey.ALL` (with human `LABELS`):

| Key | Label |
| --- | ----- |
| `name` | Full name |
| `title` | Professional title |
| `email` | Email |
| `phone` | Phone |
| `location` | Location |
| `linkedin` | LinkedIn URL |
| `github` | GitHub URL |
| `headline` | Headline |
| `summary` | Professional summary |

Tokens use `{{key}}` syntax. Substitution (`fill_placeholders`) is
**case-insensitive** and whitespace-trimmed; **unknown tokens are left intact** so a
partially configured set never corrupts a document.

## Aggregate and Cross-Context References

- The `Placeholder` is a **standalone** aggregate — it has no children.
- `placeholders.placeholders` (schema `placeholders`, table `placeholders`) holds
  `key` (unique) and `value`; there are **no foreign keys at all** — not even within
  the context — so it cannot conflict with any other bounded context (rule 15).
- Generated documents in the `application` context embed placeholder *tokens*; the
  values live here. The application router reads them via a logical reference
  (placeholder key names) and substitutes them server-side on read/export.

## Business Rules

- `GET /api/placeholders` returns the canonical `keys` (with labels), the saved
  `items`, and a flat `values` map.
- `PUT /api/placeholders` upserts a flat `{key: value}` map. Empty keys are ignored.
- `fill_placeholders(content, values)` replaces every `{{key}}` token; unknown
  tokens are preserved unchanged.
- Values are the single source for the user's personal details across all generated
  documents; editing them here updates every future PDF / preview / copy.
- Default sort is by key (rule 7 — no `created_at` column; keys are unique).

## Domain Events

See `docs/domain/placeholders/events.md` for the full EDD catalog.

# Related Documents

- `docs/domain/applications/application.md` — the consuming application context.
- `docs/ux/features/placeholders/placeholders.md` — the Placeholders page wireframe.
- `implementation-history/175_feature_placeholders_pdf.md` — this implementation.