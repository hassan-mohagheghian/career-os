# Prompt 060 - Reusable Link Display Component + Processing Drawer Fixes

## Objective

Add a reusable frontend component for displaying links and apply it to the
Processing Queue Drawer.

Job links can be very long. A raw link overflows the card, pushes layout and
is hard to use. The new component renders links correctly:

- Show only the meaningful leading characters; the rest is truncated with `...`.
- The full URL is shown in a tooltip on hover.
- The link is copyable to the clipboard.
- The link is openable in a new browser tab.

While touching the Processing Drawer, also fix its layout so the whole drawer
content stretches to full height and scrolls instead of being clipped by the
screen edge.

---

# Read Documentation First

Before making changes read:

- docs/api/processing/get-processing-queue.md
- docs/ux/features/jobs/processing-queue.md
- docs/api/jobs/get-job-detail.md (JobLinkItem shape)
- apps/frontend/src/features/jobs-v2/components/ProcessingDrawer.tsx
- apps/frontend/src/shared/ui/tooltip.tsx
- apps/frontend/src/shared/ui/sheet.tsx

---

# Architecture Rules

Follow:

- Feature-based frontend: `shared/components`, `features`, `widgets`.
- No new libraries — reuse `@radix-ui/react-tooltip`, `@phosphor-icons/react`.
- Backend stays DDD; Processing context must not own Jobs.
- No `print()`; use structlog.

---

# Current State

Links are rendered as plain `<a href target="_blank">` with `break-all`, e.g.
in `JobDetailDrawer` and `NotesLinksInput`. Long URLs overflow the container
and there is no copy affordance.

The Processing Queue Drawer (`ProcessingDrawer.tsx`) shows queue entries with a
title and current step, but no links. Its `SheetContent` is not a flex column,
so `ScrollArea` does not reliably stretch; tall content can be clipped at the
screen edge.

---

# Implementation Steps

## 1. Link Display Component

Create `apps/frontend/src/shared/components/LinkDisplay.tsx`.

Requirements:

- Props: `url: string`, `title?: string | null`, `maxLength?: number` (default 50), `className?`.
- Truncation: show the meaningful leading part of the URL (strip `https?://` and `www.` for display, then cut at `maxLength` and append `...`). Use CSS `truncate` as an extra guard.
- Tooltip: show the full URL (wrapped, `break-all`) on hover.
- Open: anchor `target="_blank" rel="noopener noreferrer"` (never `noreferrer` without `noopener`).
- Copy: dedicated icon button using `navigator.clipboard.writeText` with a legacy `execCommand` fallback; show a brief "copied" check state.
- Safety: only render a clickable anchor for `http(s)` or `mailto` URLs; never allow `javascript:` URLs.
- Export the `truncateLink` and `normalizeLinkUrl` helpers for reuse and testing.

## 2. Backend: Expose Job Links In The Queue Snapshot

`ProcessingQueueService._entry` currently returns only execution metadata. Add:

- `url`: the job's primary URL.
- `links`: parsed list of `{ title?, url }` link items.

Parse the job's `links` JSON with the same tolerance used by the jobs v2
router (JSON array / JSON scalar / plain string). The Processing context reads
the Job read-model; it does not own it.

Update `docs/api/processing/get-processing-queue.md` to document the new
fields on every entry.

## 3. Frontend Types

Update `QueueEntry` in `apps/frontend/src/entities/processing/types.ts`:

- `url: string | null`
- `links: { title?: string | null; url: string }[]`

## 4. Processing Drawer

- Add `flex flex-col` to `SheetContent` and change the `ScrollArea` to
  `flex-1 min-h-0` (drop the fixed `h-[calc(100vh-60px)]`) so the header stays
  fixed and the body stretches and scrolls.
- Render the job URL (when present) and each job link using `LinkDisplay` in
  every queue entry card.

---

# Testing Requirements

Frontend:

- `LinkDisplay.test.tsx`:
  - Truncates long URLs and keeps short URLs intact.
  - Renders the title when provided.
  - Opens with `target="_blank"` and `rel="noopener noreferrer"`.
  - Copies the URL to the clipboard and shows the copied state.
  - Renders the full URL in the tooltip content.
  - Does not render a clickable anchor for unsafe schemes (e.g. `javascript:`).
- Run `npx vitest run` in `apps/frontend`.

Backend:

- Extend `apps/backend/tests/processing/` for `ProcessingQueueService.snapshot`
  so entries include `url` and parsed `links` (JSON array, scalar, plain string).
- Run `uv run pytest apps/backend/tests/processing/ -v`.

---

# Important Constraints

- Do not change job creation/edit behavior.
- Do not introduce a new routing/state system.
- Do not copy link rendering logic into other components in this prompt;
  future prompts can migrate `JobDetailDrawer` / `NotesLinksInput` to use it.
- Follow accessibility basics: buttons carry `aria-label`, anchors carry
  `aria-label`/text content.
