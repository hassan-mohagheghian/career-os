# Session 003: Generation History, Persistence & UI Fixes

## Session Goals
- Persist generation jobs across page refreshes
- Show roadmap generations in generation history
- Add start/end datetime to generation history items
- Fix duplicate generating rows in skills page
- Show provider + session ID (copyable) in all generation UIs

## Key Findings

### DB Schema: `skill_roadmap_jobs` (shared/infrastructure/database/models/misc_models.py)
```sql
CREATE TABLE IF NOT EXISTS skill_roadmap_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    job_type TEXT NOT NULL DEFAULT 'generate',  -- generate|extend|finegrain
    status TEXT NOT NULL DEFAULT 'queued',      -- queued|running|completed|failed
    step INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 4,
    message TEXT DEFAULT '',
    version INTEGER, count INTEGER, error TEXT,
    session_id TEXT, provider_name TEXT, pid INTEGER,
    started_at TIMESTAMP, completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### WebSocket Event Payload (skill_roadmap:update)
```json
{
  "skill": "Kafka",
  "job_id": 42,
  "job_type": "generate",
  "step": 2,
  "total_steps": 4,
  "status": "running",
  "message": "Generating roadmap...",
  "session_id": "abc123...",
  "provider_name": "mimo"
}
```

### API Endpoints
| Endpoint | File | Returns |
|---|---|---|
| `GET /api/skill-roadmap-jobs` | router.py:189 | `{ items: [...] }` (active jobs, DESC) |
| `GET /api/generation-history` | dashboard.py:31 | `{ items: [...], total, offset, limit }` (merged) |
| `GET /api/skill-roadmaps/progress` | skill_roadmaps.py:57 | Job progress per skill or all |

### Frontend Architecture
- `useSkills.ts` → `skillGenJobs` state (active roadmap jobs, polling + WebSocket)
- `SkillsTab.tsx` → filters `skillGenJobs`, passes `activeJobs` to `SkillsIntelSection`
- `SkillsIntelSection.tsx` → `generatingJobMap` (Map<lowercase_name, job>) → passes full job to `SortableSkillRow`
- `SkillRoadmapDrawer.tsx` → reads `genProgress` from `/api/skill-roadmaps/progress?skill=X`
- `GenerationHistoryDrawer.tsx` → reads from `/api/generation-history`
- `SkillsIntelDashboard.tsx` → independent `activeSkillJobs` state + `generatingSkills` Set for recommendations

### Root Cause: Duplicate Generating Rows
`SkillsTab.tsx` rendered `activeJobs` twice:
1. As `GenerationProgressCard` in a separate section (lines 79-91)
2. As `genJobs={activeJobs}` passed to `SkillsIntelSection` which also shows inline indicators
→ Same job appeared in both places.

## Changes Made

### Phase 1: Persistence & History

#### 1. Fix `/skill-roadmap-jobs` response format (router.py:189)
- **Before**: Returns plain array `[dict(r) for r in rows]`
- **After**: Returns `{ items: [dict(r) for r in rows] }` with `limit` param
- **Why**: Frontend `pollActiveSkillJobs` expects `{ items: [...] }`

#### 2. Always poll active skill jobs on mount (useSkills.ts:93-100)
- **Before**: Only polled during `skills_intel` generation
- **After**: Calls `pollActiveSkillJobs()` on initial mount

#### 3. Poll while there are active jobs (useSkills.ts:159-165)
- **Before**: `if (progress.running && progress.type === 'skills_intel')`
- **After**: Also polls when `skillGenJobs` has running/queued items

#### 4. Unified generation history endpoint (dashboard.py:31-69)
- **Before**: Only queried `pending_generations` table
- **After**: Merges `pending_generations` + `skill_roadmap_jobs` with normalized fields (`source`, `title`, `started_at`, `completed_at`, `provider`)

#### 5. Show start/end datetime in history items (GenerationHistoryDrawer.tsx)
- Shows `HH:MM → HH:MM (duration)` format with tooltip for full datetime

### Phase 2: Duplicate Fix & UI Redesign

#### 6. Remove duplicate GenerationProgressCard from SkillsTab
- **Removed**: Lines 79-91 (active jobs section with `GenerationProgressCard`)
- **Removed**: Unused `GenerationProgressCard` import
- **Why**: Same jobs were shown twice — once as cards, once inline in `SkillsIntelSection`

#### 7. Pass full job data to SortableSkillRow (SkillsIntelSection.tsx)
- **Before**: `generatingSkills = Set<string>` → `isGenerating={boolean}`
- **After**: `generatingJobMap = Map<string, job>` → `generatingJob={job}`
- **Why**: Need access to `step`, `total_steps`, `message`, `provider_name`, `session_id`

#### 8. Redesign generating row in SortableSkillRow
- Shows: `Spinner` + `message` badge + `provider (session_id)` + `step/total`
- Provider+session is a **clickable button** → copies full raw session_id to clipboard
- Session ID shown in full: `mimo (abc123_def_456)`

#### 9. Redesign SkillRoadmapDrawer session ID display
- **Before**: Separate "Session:" label + code block + "Copy" link + provider badge
- **After**: Single clickable pill: `provider (full_session_id)` — copies on click

#### 10. Merge generation progress into SkillDetailDrawer
- **Before**: Clicking generating skill → opens SkillRoadmapDrawer (separate drawer)
- **After**: SkillDetailDrawer shows `GenerationProgressCard` + provider/session while generating
- Added `genProgress` state, `fetchGenProgress()`, and `skill_roadmap:update` WebSocket listener
- "Generate Roadmap" button triggers API directly and keeps drawer open
- Removed `onGenerate` prop and `selectedSkill` state from SkillsIntelSection
- Removed `SkillRoadmapDrawer` import from SkillsIntelSection (still used by SkillsIntelDashboard)

#### 10. Add session ID to GenerationHistoryDrawer
- Provider badge now shows `provider (session_id_truncated)`
- Clickable → copies full session_id to clipboard
- Added `opencode` to `PROVIDER_LABELS`

## Bugs Fixed
1. **`skill_roadmap_jobs` endpoint format mismatch** — frontend expected `{ items: [] }`, got array
2. **Roadmap jobs invisible on page refresh** — no initial poll call
3. **Roadmap jobs not in generation history** — only `pending_generations` was queried
4. **No start/end datetime shown** — only relative time was displayed
5. **Duplicate generating rows** — SkillsTab rendered activeJobs twice
6. **Session ID not copyable** — was just text, now entire badge is clickable
7. **Session ID not shown in generation list** — only shown in drawer
8. **Separate drawer for generation progress** — now shown inline in SkillDetailDrawer
9. **No action buttons for roadmap** — added Regenerate/Extend/Finegrain in SkillDetailDrawer
10. **No generation history per skill** — added `/skill-roadmaps/jobs` endpoint and history section
11. **Skill drawer not URL-addressable** — added hash-based deep linking (`#skills/Kafka`)
12. **Skill drawer too small** — resized to 1/3 of viewport width
13. **No tab separation in drawer** — added Details/Roadmap tabs
14. **Inconsistent drawer widths** — unified all drawers to `calc(100vw * 2/5)`

## Files Changed
| File | Changes |
|---|---|
| `shared/presentation/api/root_router.py` | Fixed response format, added `limit` param |
| `career/presentation/api/dashboard_router.py` | Unified history endpoint with normalized fields |
| `skills/presentation/api/skill_roadmaps_router.py` | Added `/jobs` endpoint for per-skill job history |
| `app/client/src/App.tsx` | Added `deepLinkSkill` state, hash parsing for `#skills/{name}`, passed to SkillsTab |
| `app/client/src/features/skills/components/SkillsTab.tsx` | Accepts `deepLinkSkill` prop, passes to SkillsIntelSection |
| `app/client/src/features/insights/components/SkillsIntelSection.tsx` | `generatingJobMap`, hash-based drawer open/close, deep link handling |
| `app/client/src/features/insights/components/SkillDetailDrawer.tsx` | URL-addressable drawer (2/5 width), Details/Roadmap tabs, progress, actions, generation history |
| `app/client/src/features/insights/components/SkillRoadmapDrawer.tsx` | Redesigned session ID as clickable pill (full raw ID), unified 2/5 width |
| `app/client/src/features/jobs/components/drawer/JobDrawer.tsx` | Unified to 2/5 width |
| `app/client/src/features/companies/components/CompanyDrawer.tsx` | Unified to 2/5 width |
| `app/client/src/shared/components/WorkflowTerminal.tsx` | Unified to 2/5 width |
| `app/client/src/shared/components/GenerationHistoryDrawer.tsx` | Added session ID, `opencode` label, copy support (full raw ID), unified 2/5 width |

## Pending / Future Work
- Consider real-time updates for history drawer (currently only polls on open)
- Add elapsed time to generating rows in SortableSkillRow
