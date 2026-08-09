# Prompt 134 - Remove old company score breakdown cards

## Objective

Remove the three legacy full-width score breakdown cards (Overall grade card,
Fit score card, Success score card) plus the Score Calculation card from the
Company Detail drawer. The header score strip (grade badge + Fit / Success /
Overall cards + Why explanation popover) is now the single score display,
mirroring the Job Detail drawer.

## Current State

- Company Detail drawer header shows the grade badge, Fit / Success / Overall
  score cards, and a **Why** button that opens the scores explanation popover
  (`CompanyScoresExplanationButton`, hover-open / click-pin / unhover-close).
- A legacy bottom `CompanyScoresSection` still rendered three big cards
  (Overall Grade, Company Fit Score, Company Success Score) with positive /
  negative factors and a Score Calculation row — duplicating the header info.

## Changes

- `apps/frontend/src/features/companies-v2/components/CompanyDetailDrawer.tsx`:
  - Deleted the `CompanyScoresSection` component and its usage in
    `CompanyDetailContent`.
- `apps/frontend/src/features/companies-v2/components/CompanyDetailDrawer.test.tsx`:
  - Replaced the "no-scores placeholder" test (placeholder lived in the removed
    section) with an assertion that no score cards / explanation button render
    for unprocessed companies.
- `docs/ux/features/companies/company-detail.md`:
  - Rewrote the Scores section to document the Why explanation popover and note
    the removal of the old breakdown cards.
  - Updated the drawer layout wireframe placeholder.
- `docs/ux/features/companies/page.md`, `DESIGN.md`: replaced "Full score
  breakdown with factors and calculation" / "Scores breakdown" references with
  the scores explanation popover.

## Verification

Frontend:

    cd apps/frontend && npx vitest run   # 515 pass
    npx tsc --noEmit                      # clean

## Constraints

- No version bump (feature batched at release).
- The header score strip + Why popover is the single score display; no duplicate
  breakdown sections.
