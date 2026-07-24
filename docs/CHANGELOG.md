# Changelog

## [Unreleased] — Skill Intelligence System

### Added
- **Skill Taxonomy** — 5 categories: Technical, Engineering, Professional, Domain, Career
  - Category tabs with filtering across all sections
  - Auto-categorization of existing skills via migration
- **Skill Aliases** — `skill_aliases` table for merged skills
  - Canonical skill + alias records (e.g., PostgreSQL → Postgres)
  - Aliases shown as "Variant" badges in UI
- **Skill Relationships** — `skill_relationships` table
  - Related, similar, parent, child, alternative types
- **Skill Detail Drawer** — Full skill overview with:
  - Category, confidence, market demand
  - Evidence (why this skill matters)
  - Merged variants display
  - Checkable learning roadmap
  - Rename, hide, remove actions
- **Skill Management Endpoints**:
  - `PATCH /api/tech-stack/:id/hide` — hide skill
  - `PATCH /api/tech-stack/:id/restore` — restore hidden skill
  - `PATCH /api/tech-stack/:id/rename` — rename skill
  - `DELETE /api/tech-stack/:id` — delete skill + aliases
  - `POST /api/tech-stack/merge` — merge skills via drag-and-drop
  - `GET /api/tech-stack/hidden` — list hidden skills
  - `GET/POST/DELETE /api/skill-relationships` — relationship CRUD
- **WebSocket Real-Time Updates**:
  - Pending jobs/companies: `pending:update`, `pending:log`, `pending:complete`, `pending:error`
  - Career intelligence: `career_intel:progress` with session_id
  - Session ID extraction from mimo output (all 5 variants + fallback)
- **Prompt Organization**:
  - `career_intel/` — career_intelligence.txt, skills_intelligence.txt
  - `skill_roadmaps/` — generate, extend, finegrain prompts
  - `job_processing/` — step2-8 pipeline prompts
  - `company/` — extract, analyze prompts
  - `resume/` — resume, cover letter prompts
- **Test Structure** — Mirrors server structure:
  - `tests/test_blueprints/` — dashboard, pending, companies
  - `tests/test_services/` — worker, company_worker, process/*
  - `tests/test_core/` — queue
  - `tests/test_process/` — skill_management (12 tests)

### Changed
- **SkillsIntelSection Redesign**:
  - Two-column layout: Strengths (top) | Gaps + Recommendations
  - Category tabs filter all sections
  - Add Custom Skill inline with category tabs (collapsible)
  - Merge mode with drag-and-drop across all sections
  - Every skill shows source badge (Custom/AI)
  - Alias "Variant" badges under merged skills
- **SkillDetailDrawer** — New component with rename, checkable roadmap, variants
- **Market Intelligence** — Countries in compact right sidebar, scrollable cities
- **Consistent tab styling** — All drawers use `bg-muted` TabsList
- **Worker broadcasting** — `worker.py` and `company_worker.py` emit SocketIO events
- **Broadcaster logging** — `[ws]` prefix for all events in terminal

### Fixed
- ProcessingItem `workflow_log` JSON.parse crash (handles array/string)
- `session_id` overwritten by numeric `val` in WebSocket handler
- Career intelligence polling removed (WebSocket replaces it)
- JSX syntax errors (stray `)}`, missing imports)

## [Previous]

### Added
- Career Intelligence module — 6 sections with AI analysis
- WebSocket real-time processing output
- SSE for pending items streaming
- Configurable scoring rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING)
- Resume/cover letter generation via Mimo CLI
- LinkedIn profile integration
- Job reprocessing and rescoring
