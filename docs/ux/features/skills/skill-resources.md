# Skill Resources (Notes & Links)

## Purpose

Notes and links let users track their learning progress for each skill. Notes
are free-text activity entries (what was learned, what to study next). Links
are titled resource URLs (documentation, tutorials, references) where the
title identifies the resource and the URL points to the page.

Both appear in the Skill Detail Drawer between the Evidence section and the
Referenced Jobs section.

---

# Related Page

Located in: `features/skills/page.md`

Related:

- `features/skills/skill-detail.md`

---

# User Goals

The user should be able to:

- Add a note to a skill to track learning progress
- Delete a note from a skill
- Add a titled link (title + URL) to save documentation or references
- Delete a link from a skill
- See notes and links listed in the skill detail drawer

---

# Notes Section

```text
┌─────────────────────────────────────┐
│ NOTES                               │
│                                     │
│ Learned decorators and context      │
│ managers today. Need to study       │
│ async/await next.                   │
│ 2 hours ago                         │
│─────────────────────────────────────│
│ Reviewed SQL joins and window       │
│ functions. Feeling confident.       │
│ Yesterday                           │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ What did you learn? What should │ │
│ │ you study next?                 │ │
│ └─────────────────────────────────┘ │
│                    [ Plus Add Note ] │
└─────────────────────────────────────┘
```

- Notes are listed newest first.
- Each note shows content + creation timestamp.
- Hover reveals a delete (trash) button.
- Enter submits (Shift+Enter for newline).
- Empty content is rejected.

---

# Links Section

```text
┌─────────────────────────────────────┐
│ LINKS                               │
│                                     │
│ 🔗 Official Docs                   │
│    https://docs.python.org/3/       │
│                                     │
│ 🔗 Real Python Tutorial            │
│    https://realpython.com/          │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Title (e.g. Official Docs)      │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ URL (https://...)               │ │
│ └─────────────────────────────────┘ │
│                    [ Plus Add Link ] │
└─────────────────────────────────────┘
```

- Links are listed newest first.
- Each link shows a clickable title (opens in new tab) + URL below.
- Hover reveals a delete (trash) button.
- Title and URL are both required.
- Enter in the URL field submits.

---

# Data Model

## skill_notes

| Column     | Type     | Description                     |
| ---------- | -------- | ------------------------------- |
| id         | integer  | PK, auto-increment              |
| skill_id   | integer  | FK → skill.skills.id            |
| content    | text     | Free-text note content          |
| created_at | text     | ISO timestamp                   |
| updated_at | text     | ISO timestamp                   |

## skill_links

| Column     | Type     | Description                     |
| ---------- | -------- | ------------------------------- |
| id         | integer  | PK, auto-increment              |
| skill_id   | integer  | FK → skill.skills.id            |
| title      | string   | Display name for the resource   |
| url        | string   | URL to the resource             |
| created_at | text     | ISO timestamp                   |

Both tables live in the `skill` schema (same bounded context as skills).

---

# API

## Notes

```
POST /api/skills/{id}/notes
{ "content": "Learned decorators today" }

DELETE /api/skills/notes/{note_id}
```

## Links

```
POST /api/skills/{id}/links
{ "title": "Official Docs", "url": "https://docs.python.org" }

DELETE /api/skills/links/{link_id}
```

Notes and links are also included in `GET /api/skills/{id}` response.

---

# Accessibility

- Delete buttons use `aria-label` for screen readers.
- Links open in new tab with `rel="noopener noreferrer"`.
- Textarea uses Enter to submit, Shift+Enter for newline.

---

# Related Documents

- `features/skills/page.md`
- `features/skills/skill-detail.md`
