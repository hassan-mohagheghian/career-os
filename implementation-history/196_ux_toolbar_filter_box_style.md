# Prompt 196 - UX: make Recommendation/Tracking filter boxes match toolbar styling

## Objective

The Recommendation and Tracking multi-select filters in the Jobs toolbar must
visually match the other toolbar filter boxes (Status, Remote, Visa, Date) and
show a selection **count badge** when items are selected.

## Current State

- `apps/frontend/src/features/jobs-v2/components/MultiSelectFilter.tsx` rendered
  its trigger as a borderless `inline-flex ... text-primary` button that showed
  the joined selection labels (e.g. "Apply, Consider") when active.
- The other toolbar filters use shadcn `SelectTrigger` (`shared/ui/select.tsx`):
  a bordered box (`border border-input bg-transparent`), `h-7`, and a
  `RiArrowDownSLine` chevron appended via `SelectPrimitive.Icon`.
- `JobsToolbar.tsx` uses `<MultiSelectFilter label="Recommendation" ... />` and
  `<MultiSelectFilter label="Tracking" ... />`.
- `JobsToolbar.test.tsx` asserted the joined label appeared in the trigger
  ("shows the selected recommendation label when active" → `Consider`).

## Changes

1. `MultiSelectFilter.tsx`: restyle the trigger button to mirror `SelectTrigger`
   (`h-7 rounded-none border border-input bg-transparent px-2.5 text-2xs
   text-primary hover:bg-muted ...`); add a `RiArrowDownSLine` chevron
   (imported from `@remixicon/react`); always show the `label`; when
   `selected.length > 0` render a small emerald count badge with the number of
   selected values (drop the joined-label text to keep the box compact).
2. `JobsToolbar.test.tsx`: update the two "shows the selected ... label when
   active" tests to assert the count badge (`getByText('1')`) instead of the
   joined label.
3. `docs/ux/features/jobs/page.md`: update the Recommendation/Tracking Filter
   ASCII wireframes to show the bordered box + `[n]` count badge and note the
   trigger mirrors the other filter boxes.

## Testing Requirements

- `cd apps/frontend && npx vitest run src/features/jobs-v2/components/JobsToolbar.test.tsx` pass.
- Visual: Recommendation/Tracking boxes now have a border + down chevron like
  Status/Remote/Visa/Date; selecting values shows a numbered badge.

## Constraints

- Match existing `SelectTrigger` styling tokens (border, height, chevron), no
  new design language.
- Keep OR-multi-select behavior and the popover unchanged.
- Respect AGENTS.md rule 13: UX docs + wireframe updated.
