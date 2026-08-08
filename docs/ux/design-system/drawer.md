# Drawer

## Purpose

The Drawer is a reusable layout component based on **shadcn/ui Drawer / Sheet**.

It provides a secondary workspace without navigating away from the current page.

Typical use cases:

- View details
- Edit entities
- Monitor background processing
- Display forms
- Show contextual information

A Drawer should never replace the primary page content.

---

# Design Principles

- Reusable across the entire application
- Consistent behavior on every page
- Configurable size
- Configurable placement
- Mobile friendly
- Keyboard accessible
- Built on top of shadcn/ui

---

# Variants

| Variant | Width | Typical Usage              |
| ------- | ----: | -------------------------- |
| xs      | 320px | Confirmations, small forms |
| sm      | 420px | Filters, simple forms      |
| md      | 560px | —                          |
| lg      | 720px | Entity detail/edit panels  |
| xl      | 960px | —                          |
| full    |  100% | Mobile or full workspace   |

Widths are design tokens and may change globally.

Pages should reference only the variant name.

**Default is `lg`.** Consumers must not override the variant — only the
default (`lg`) is used across the application, so all drawers share a
consistent width.

---

# Placement

Supported placements:

- Right (default)
- Left
- Bottom

Top placement is not supported.

---

# Responsive Behavior

## Desktop

Drawer slides from the selected side.

The underlying page remains visible.

---

## Tablet

Drawer width adapts to the selected variant.

---

## Mobile

All variants become **full-screen** by default.

---

# Standard Structure

```text
┌──────────────────────────────────────────────────────────────┐
│ Header                                            [Close]    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Content                                                      │
│                                                              │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Footer (Optional)                                            │
└──────────────────────────────────────────────────────────────┘
```

---

# Anatomy

```
Drawer

├── Header
│   ├── Title
│   ├── Description (Optional)
│   └── Close Button
│
├── Content
│
└── Footer (Optional)
```

---

# Header Close Button Clearance

The vaul-based `Drawer` shell lays its close button out in normal flex flow, so
it never overlaps header content. The legacy `Sheet`-based drawers were
deprecated in favor of the unified vaul `Drawer`; any header action button
(rendered via the `actions` slot) sits to the left of the close button without
reserving extra space.

---

# Properties

| Property          | Description              |
| ----------------- | ------------------------ |
| Variant           | xs, sm, md, lg, xl, full |
| Placement         | right, left, bottom      |
| Title             | Drawer title (ReactNode) |
| Description       | Optional subtitle        |
| Actions           | Optional header action area |
| Footer            | Optional action area     |
| Close Button      | Optional                 |
| Scrollable        | Yes                      |
| contentClassName  | Optional content styling |

---

# Behavior

The Drawer should:

- Open without page navigation
- Preserve page state
- Preserve page scroll position
- Close with Escape
- Support outside-click closing (configurable)
- Trap keyboard focus while open
- Restore focus after closing

---

# Accessibility

- Keyboard accessible
- Focus trap
- Escape closes drawer
- Screen-reader friendly
- Proper ARIA attributes provided by shadcn/ui

---

# Usage

Every drawer in the application uses the **default `lg` variant** and does not
override it. Only placement may vary where the design calls for it.

## Processing Queue

Variant

```
lg (default)
```

Placement

```
right
```

---

## Job Details / Job Edit

Variant

```
lg (default)
```

Placement

```
right
```

---

## Company Details / Company Edit

Variant

```
lg (default)
```

Placement

```
right
```

---

## Skill Detail / Add / Edit Skill

Variant

```
lg (default)
```

Placement

```
right
```

---

## Generation History

Variant

```
lg (default)
```

Placement

```
right
```

---

## Mobile Navigation

Variant

```
lg (default)
```

Placement

```
left
```

---

## Rule Form (Add / Edit Rule)

Variant

```
lg (default)
```

Placement

```
bottom
```

---

## Resume Preview

Variant

```
lg (default)
```

Placement

```
right
```

---

# Implementation Notes

Framework

- Next.js
- React

UI Library

- shadcn/ui

Underlying Component

- `Drawer` (vaul, via `@/shared/ui/drawer`)

The application exposes a single reusable `Drawer` component
(`@/shared/components/Drawer`) that wraps the vaul primitives and provides a
consistent API across the project. The legacy `Sheet`-based drawers
(`@/shared/ui/sheet`, `DrawerComponents`) are deprecated and removed.

---

# Future Enhancements

Potential future capabilities:

- Resizable drawer
- Nested drawers
- Persistent drawers
- Unsaved changes protection
- URL-synchronized drawers
- Multi-step workflows

---

# Related Documents

- `docs/ux/design-system/README.md`
- `docs/ux/features/jobs/page.md`
- `docs/ux/features/jobs/job-row.md`
