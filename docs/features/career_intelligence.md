# Career Intelligence

AI-powered career insights system with 6 sections, concurrency control, real-time progress tracking, and terminate capability.

## Sections

| Section | Purpose |
|---------|---------|
| Overview | Career health score (0-100), position cards, prioritized next actions |
| Opportunities | Job funnel (Apply Now → Low Priority), best jobs, missed opportunities |
| Companies | Product vs Recruiting company rankings with fit scores |
| Skills | Strengths, gaps, learning ROI recommendations |
| Market | Country/city analysis, remote opportunities, visa friendliness |
| Networking | Connection strategy, LinkedIn search queries per company |

## Backend

- **Service**: `services/career_intel.py` — generation with concurrency lock and cancel support
- **Blueprint**: `blueprints/career_intel.py` — REST API
- **Prompt**: `prompts/career_intelligence.txt` — AI prompt template
- **Tables**: `career_insight_runs` (workflow), `career_insights` (results)

### Concurrency Control
- Only one analysis runs at a time (threading lock)
- HTTP 409 if another request comes in while running
- Stale processing records (>5 min) auto-cleaned on status check

### Cancel/Terminate
- `POST /api/career-intelligence/cancel` — terminates the running Mimo subprocess
- Uses `subprocess.Popen` + `proc.terminate()` to kill the AI process
- Sets `_cancel_requested` flag, checked after mimo returns
- Marks run as `cancelled` in DB (not `failed`)

### API Endpoints
```
GET  /api/career-intelligence              — all sections
GET  /api/career-intelligence/<section>    — one section
GET  /api/career-intelligence/progress     — real-time progress + cancellable flag
GET  /api/career-intelligence/status       — per-section status + _running flag
GET  /api/career-intelligence/runs         — generation history
POST /api/career-intelligence/refresh      — generate all (background)
POST /api/career-intelligence/<section>/refresh — generate one (background)
POST /api/career-intelligence/cancel       — terminate running analysis
```

## Frontend

- **Tab**: `components/career-intel/CareerIntelTab.jsx`
- **Hook**: `hooks/useCareerIntel.js` — state, polling, progress, cancel
- **Sections**: OverviewSection, OpportunitiesSection, CompaniesSection, SkillsIntelSection, MarketIntelSection, NetworkingIntelSection

### Progress Card (shown during analysis)
- Step icons with status (done/active/pending)
- Progress bar with elapsed time
- LIVE badge
- **Terminate button** (red, X icon) — calls cancel endpoint
- Shows which type is running (e.g., "All sections")

### Progress Steps
1. Collecting data → 2. AI analysis → 3. Calculating metrics → 4. Saving results → 5. Complete
