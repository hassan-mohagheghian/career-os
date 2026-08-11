# Add / Edit Rule Drawer

## Purpose

A **right-side drawer** (placement `right`, `lg` variant — the same side as
every other drawer in the app) used for both adding a new rule and editing an
existing one. It slides in from the right edge over the Rules page without
leaving it. The title switches between `Add Rule` and `Edit Rule`.

The drawer is implemented in
`apps/frontend/src/features/rules/components/RuleFormDrawer.tsx`, built on the
shared `Drawer` primitive (`docs/ux/design-system/drawer.md`).

---

## Wireframe

```text
                     ┌──────────────────────────────────────────────┐
                     │ Add Rule / Edit Rule                [Close] ✕│
                     ├──────────────────────────────────────────────┤
                     │ Scope ▼        Category ▼                    │
                     │ ┌───────────┐  ┌───────────┐                 │
                     │ │ Job ▾     │  │ Fit score ▾│                │
                     │ └───────────┘  └───────────┘                 │
                     │                                              │
                     │ Key name *                                   │
                     │ ┌────────────────────────────────────────┐  │
                     │ │ e.g. remote_work                       │  │
                     │ └────────────────────────────────────────┘  │
                     │                                              │
                     │ Priority (0-100)                            │
                     │ ┌────────────────────────────────────────┐  │
                     │ │ 50                                     │  │
                     │ └────────────────────────────────────────┘  │
                     │                                              │
                     │ Value / rule *                              │
                     │ ┌────────────────────────────────────────┐  │
                     │ │ How the rule matches candidates /       │  │
                     │ │ companies                               │  │
                     │ └────────────────────────────────────────┘  │
                     │                                              │
                     │ How this affects scoring (optional)          │
                     │ ┌────────────────────────────────────────┐  │
                     │ │ Optional description                   │  │
                     │ └────────────────────────────────────────┘  │
                     │                                              │
                     │                              [Cancel] [Save] │
                     └──────────────────────────────────────────────┘
```

## Fields

| Field                    | Control  | Required | Notes                                                         |
| ------------------------ | -------- | -------- | ------------------------------------------------------------- |
| Scope                    | Select   | yes      | Shared / Job / Product Company / Recruiting                   |
| Category                 | Select   | yes      | `fit` (Fit score) or `success` (Success score)                |
| Key name                 | Text     | yes      | Unique key, e.g. `remote_work`                                |
| Priority (0-100)         | Number   | no       | The single priority: list order + severity badge + LLM weight |
| Value / rule             | Textarea | yes      | The rule instruction text                                     |
| How this affects scoring | Text     | no       | Optional human-readable description                           |

> **Priority** is the single rule value that drives list order, the severity
> badge (≥90 Critical, ≥75 High, ≥50 Med, else Low) and the `w:{n}` weight fed
> into LLM scoring prompts. It can be set directly in the drawer or tuned
> afterwards with the Move up / Move down buttons / drag-and-drop on the Rules
> page (see `page.md`).

## Validation

- **Save** is disabled until both `key` and `value` are non-empty.
- Saving the same `key` twice for a category is prevented by the backend unique
  constraint on `(category, key)`.
- **Save** uses the shared primary button variant (`variant="default"`,
  `size="sm"`) — the same design-token save button as every other drawer.
  **Cancel** uses `variant="outline"`.

## Behavior

- **Add mode**: the drawer opens empty with defaults — Scope = the column the
  user clicked **Add rule** in, Category = `fit`, Priority = 50.s
- **Edit mode**: the drawer is prefilled with the clicked rule; saving updates
  `value`, `description`, `scope` and `priority` (enabled is untouched).
- **Save**: fires `PUT /api/rules/{id}` (edit) or `POST /api/rules` (add), then
  closes and refreshes the list.
- **Cancel / Close**: discards changes and closes the drawer.

## Empty / Error States

The drawer itself has no empty state. Save button shows disabled until the form
is valid. API errors are not surfaced inside the drawer (the list refetches
regardless).
