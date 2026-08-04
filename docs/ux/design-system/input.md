# Debounced Input

## Purpose

`DebouncedInput` is the **only** component to use for text search / filter inputs.

It wraps the shadcn **Input** primitive and defers `onValueChange` until the user
pauses typing. This prevents a server request on every keystroke, which keeps the
backend responsive when search is performed server-side.

Typical use cases:

- Text search boxes (e.g. jobs page: "Search by title, company, or keyword")
- Text filter fields (e.g. jobs page: "Location")
- Any future drawer, sheet, or page search/filter input

Rules:

- **All text search/filter inputs must use `DebouncedInput`.**
- Select / dropdown filters are instant by design and must **not** be debounced.
- Form fields (title, notes, URLs) are not search and must **not** be debounced.

---

# Behavior

## Default delay

Typing updates the visible value **immediately**; `onValueChange` fires only after
the user stops typing for the debounce delay.

- Default delay: **300ms**
- Per-input override: `debounceMs`
- Each new keystroke resets the pending timer (a single call is emitted per pause).

## Clearing

Clearing is immediate:

- The built-in ✕ clear button (when `clearable`) fires `onValueChange('')` at once
  and cancels any pending debounce.
- Pressing `Escape` in the input behaves like the ✕ button.
- The ✕ button is shown only while the input is non-empty.

## External resets

When the parent resets `value` (e.g. a toolbar "Clear" action that clears several
filters at once), the component:

- syncs its visible value to the new prop, and
- cancels any pending debounce so a stale request cannot re-populate the input.

## Unmount

Pending timers are cleared on unmount; no `onValueChange` fires after unmount.

---

# Usage

```tsx
import { DebouncedInput } from '@/shared/ui/debounced-input'
import { MagnifyingGlass } from '@phosphor-icons/react'

<DebouncedInput
  value={query}
  onValueChange={setQuery}
  placeholder="Search by title, company, or keyword..."
  debounceMs={300}
  icon={<MagnifyingGlass className="w-3.5 h-3.5 text-muted-foreground" />}
  clearable
  clearLabel="Clear search"
  activeClassName="border-emerald-500/30"
  wrapperClassName="w-full"
  inputClassName="pl-8 h-7 text-xs"
  aria-label="Search jobs"
/>
```

`onValueChange` must update the parent state that drives the data request. For
TanStack Query, include the debounced value in the `queryKey` so the request
refetches only after the debounce settles.

---

# Props

| Prop              | Type                     | Default | Description                                                          |
| ----------------- | ------------------------ | ------- | -------------------------------------------------------------------- |
| `value`           | `string`                 | —       | Controlled value (external resets are synced).                       |
| `onValueChange`   | `(value: string) => void`| —       | Fired after the debounce delay (or immediately on clear).            |
| `debounceMs`      | `number`                 | `300`   | Delay before `onValueChange` fires after typing pauses.              |
| `icon`            | `ReactNode`              | —       | Leading icon, absolutely positioned inside the input.                |
| `clearable`       | `boolean`                | `false` | Show a ✕ clear button while the input is non-empty.                  |
| `clearLabel`      | `string`                 | `"Clear input"` | `aria-label` for the clear button.                            |
| `activeClassName` | `string`                 | —       | Applied to the input while it is non-empty (e.g. highlight border).  |
| `wrapperClassName`| `string`                 | —       | Extra classes for the relative wrapper div.                          |
| `inputClassName`  | `string`                 | —       | Extra classes for the inner input.                                   |
| `...`             | `InputHTMLAttributes`    | —       | Passed to the inner input (`placeholder`, `aria-label`, etc.).       |

---

# Design Principles

- Reusable across the entire application (single source of truth for debounce).
- Instant visual feedback while typing.
- No server pressure during continuous typing.
- Keyboard accessible (Escape clears).
- Built on top of the shadcn Input primitive.
