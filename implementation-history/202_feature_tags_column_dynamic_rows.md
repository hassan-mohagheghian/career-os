# Prompt 202 - Tags Column with Dynamic Row Heights

## Objective

Add a dedicated Tags column to the job list, move dismissed/visa/easy_apply badges into it alongside user-defined tags, add tags editing in the Edit Job drawer, and make all row columns support dynamic double-height rows with truncation + expand icon.

## Current State

- Grid template: `jobsColumns.ts:1` — 9 columns: Title, Company, Location, Scores, Rec, Status, Tracking, Updated, Created
- Company column: `minmax(140px, 1.4fr)` — takes significant width
- Tags badges are scattered: dismissed in Status col (`JobRow.tsx:114-121`), visa in Location col (`:87-91`), easy_apply in Location col (`:92-96`)
- `JobListItem` already has `tags: string[]` (`types.ts:124`) and `JobEditInput` has `tags?: string[]` (`:307`)
- Edit drawer (`JobEditDrawer.tsx`) does NOT have a Tags field yet
- Virtualizer uses fixed `estimateSize: () => 40` (`JobsTable.tsx:81`) — no dynamic row heights
- No truncation/expand mechanism exists for cell content

## Changes

### 1. New component: `ClampText.tsx`
- `apps/frontend/src/features/jobs-v2/components/ClampText.tsx`
- Renders text with `line-clamp-2` (max 2 lines)
- Uses `useRef` + `useEffect` to detect if content overflows 2 lines
- Shows `CaretDown` icon at end when truncated
- Props: `text: string`, `className?: string`

### 2. Update grid template: `jobsColumns.ts`
- Narrow Company: `minmax(140px, 1.4fr)` → `minmax(100px, 1fr)`
- Add Tags column after Rec: `minmax(160px, 1.5fr)`
- New template: `minmax(200px, 2fr) minmax(100px, 1fr) minmax(140px, 1.4fr) 210px 80px minmax(160px, 1.5fr) 120px 110px 90px 90px`

### 3. Update `JobsTable.tsx`
- Add `Tags` to `COLUMN_DEFS` array (after Rec)
- Change virtualizer to use `measureElement` for dynamic row heights
- Remove fixed height from row wrapper, let grid determine height
- Add `data-index` attribute to row wrapper for virtualizer measurement
- Update skeleton rows to match new column count

### 4. Update `JobRow.tsx`
- Remove visa badge from Location column (`:87-91`)
- Remove easy_apply badge from Location column (`:92-96`)
- Remove dismissed badge from Status column (`:114-121`) — show ProcessingStatus always
- Add new Tags column cell after Recommendation:
  - User-defined `job.tags` as compact badges
  - If `job.dismissed`: red "Dismissed" badge
  - If `job.visa_sponsorship`: blue "Visa" badge
  - If `job.easy_apply`: sky "Easy Apply" badge
- Wrap each cell's text content with `ClampText` for truncation + expand icon
- Add `ref={virtualizer.measureElement}` and `data-index={index}` for dynamic measurement
- Update `items-center` to `items-start` on row grid for multi-line support

### 5. Update `JobEditDrawer.tsx`
- Add `tags` state (initialized from `detail.tags`)
- Add Tags field UI after Description:
  - Shows existing tags as removable badges
  - Input + Plus button to add new tags
  - Tags are free-form strings (no predefined set)
- Include `tags` in the save payload

### 6. Update docs
- `docs/ux/features/jobs/job-row.md`: Update layout to include Tags column, document truncation behavior
- `docs/ux/features/jobs/page.md`: Update column table, add Tags column, document dynamic row heights
- `docs/ux/features/jobs/edit-job.md`: Add Tags field to form structure
- `docs/ux/features/jobs/job-tags.md`: Update to reflect Tags column now also shows visa/easy_apply/dismissed

### 7. Update tests
- `JobRow.test.tsx`: Update for new Tags column, verify tags/badges rendering
- `JobEditDrawer.test.tsx`: Add tags editing tests

## Testing Requirements

```bash
cd apps/frontend && npx vitest run
cd apps/frontend && npm run lint
cd apps/frontend && npm run typecheck
```

## Constraints

- Frontend TypeScript only
- No cross-context imports
- Follow existing badge styling conventions
- Virtualizer dynamic height must not break infinite scroll
- `ClampText` must be lightweight (no extra deps)
