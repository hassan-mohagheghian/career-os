# Prompt 122 - Chore: Consistent toolbar control heights (fix Select height override)

## Objective

Make every control in the toolbox section of the Jobs, Companies and Skills
pages render at the same compact height. The search/location inputs and the
action buttons (Pinned, Columns, Clear) already render at `h-7` (28px), but the
filter dropdowns (`SelectTrigger`) silently render at `h-10` (40px) because the
toolbar's `h-7` class was dead. This made the dropdowns visibly taller than the
other controls in the same row.

## Root cause

`SelectTrigger` in `src/shared/ui/select.tsx` sized itself through
data-attribute variants:

```
data-[size=default]:h-10 data-[size=sm]:h-9
```

Every call site overrides height with a plain class (`h-7` in the toolbars,
`h-8` in the drawers). `tailwind-merge` keeps both the plain `h-7` class AND
the `data-[size=default]:h-10` class because they live in different modifier
groups, and the data-variant rule wins on CSS specificity (attribute selector +
class beats a plain class). Result: every `SelectTrigger` rendered at 40px
regardless of the intended height.

## Implementation steps

1. `apps/frontend/src/shared/ui/select.tsx`: replace
   `data-[size=default]:h-10 data-[size=sm]:h-9` with a plain conditional class
   placed before `className` in the `cn()` call:

   ```tsx
   size === "sm" ? "h-9" : "h-10",
   ```

   `tailwind-merge` now dedupes the default `h-10`/`h-9` against a call-site
   `h-7`/`h-8` (both plain height utilities, same group), so the call-site
   height wins and the design-system defaults are preserved when no height is
   passed. The `data-size` attribute stays for any consumers that key off it.

2. `apps/frontend/src/shared/ui/select.test.tsx` (new): regression tests
   asserting the default trigger renders `h-10`, `size="sm"` renders `h-9`, and
   an explicit `h-7` override is kept while the `data-[size=*]` height classes
   are gone.

## Why the Columns button was already consistent

`ColumnsDropdown` triggers a `Button` with `variant="ghost" size="sm"` plus
`h-7 w-auto gap-1 text-2xs` — same classes as Pinned/Clear. `Button` uses plain
cva height classes (`h-9` for `sm`), so its `h-7` override already worked via
`tailwind-merge`; it now matches the fixed dropdown triggers.

## Outcome

All toolbar controls — search input, location input, filter dropdowns
(Status / Remote / Visa / Recommendation / Industry / Category), Pinned,
Columns and Clear — render at `h-7` (28px). Drawer selects (`h-8`, 32px) now
render at their intended height instead of 40px.

## Testing

- New: `src/shared/ui/select.test.tsx` (3 tests).
- `npx vitest run` — 58 files / 459 tests pass.
- `npx tsc --noEmit` — no new errors.
