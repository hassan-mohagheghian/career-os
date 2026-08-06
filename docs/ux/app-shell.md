# App Shell — Header Navigation

## Purpose

The app shell provides the top-level navigation. Navigation is a single
**top header menu**; there is no left sidebar. Clicking a menu item never hides
the menu — the header is always visible on desktop.

---

# Anatomy

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ ☰  Job Search   Jobs  Companies  Skills  Resume  Rules  AI ▾    [🌙] [☰]  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                               page content                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

AI dropdown:
┌──────────────┐
│ LLM Configurations │
└──────────────┘
```

| Element            | Behavior                                              |
| ------------------ | ----------------------------------------------------- |
| `☰` (mobile only) | Opens the mobile nav sheet (left).                    |
| Job Search brand   | Navigates to `/jobs`.                                 |
| Top-level items    | Navigate to `/{id}` (`jobs`, `companies`, `skills`, `resume`, `rules`). |
| `AI ▾`             | Dropdown submenu → `LLM Configurations` (`/ai/llm-configurations`). |
| Theme toggle       | Switches light/dark.                                  |
| History button     | Opens the Generation History drawer.                  |

---

# States

## Active item

The item matching the current route (`/pathname[1]`) is highlighted with a
primary background tint + primary text; its sub-item (e.g. LLM Configurations on
`/ai/llm-configurations`) is marked primary in the dropdown.

## Clicking the active item

Pushes the same route again — a no-op navigation. The menu **stays visible** on
desktop (no collapse, no reload needed).

## Mobile

The top menu is hidden below `md`; a hamburger opens a left sheet with the same
items, including the `AI` submenu expanded inline. Selecting any item navigates
and closes the sheet.

---

# Behavior Rules

- `handleNav(id, childId?)` → `router.push(childId ? /{id}/{childId} : /{id})`;
  on mobile it also closes the sheet.
- Submenu items render via a shadcn `DropdownMenu`; the active sub-item is
  highlighted.
- Header is `fixed top-0 h-12` and full-width; page content scrolls beneath it
  with `pt-16` clearance.

---

# Related Documents

- `docs/ux/features/jobs/page.md` (page content under the shell)
- `docs/ux/features/companies/page.md`
- `docs/ux/features/skills/page.md`
- `DESIGN.md` (navigation structure wireframe)
