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
| md      | 560px | Processing Queue           |
| lg      | 720px | Company Details            |
| xl      | 960px | Job Details, Editors       |
| full    |  100% | Mobile or full workspace   |

Widths are design tokens and may change globally.

Pages should reference only the variant name.

Default is lg.

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

# Properties

| Property     | Description              |
| ------------ | ------------------------ |
| Variant      | xs, sm, md, lg, xl, full |
| Placement    | right, left, bottom      |
| Title        | Drawer title             |
| Description  | Optional subtitle        |
| Footer       | Optional action area     |
| Close Button | Optional                 |
| Scrollable   | Yes                      |

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

## Processing Queue

Variant

```
md
```

Placement

```
right
```

---

## Job Details

Variant

```
xl
```

Placement

```
right
```

---

## Company Details

Variant

```
lg
```

Placement

```
right
```

---

## Resume Preview

Variant

```
full
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

- `Sheet` (recommended for desktop side panels)
- `Drawer` (recommended for mobile bottom sheets)

The application should expose a single reusable `Drawer` component that wraps the appropriate shadcn/ui primitives and provides a consistent API across the project.

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

- `docs/ux/design-system/layout.md`
- `docs/ux/design-system/buttons.md`
- `docs/ux/pages/jobs.md`
- `docs/ux/pages/companies.md`
