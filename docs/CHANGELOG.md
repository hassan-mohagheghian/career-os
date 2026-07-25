# Changelog

## [2.2.0] — 2026-07-25

### Added
- **AI Agent Orchestration Layer** — Provider abstraction, LLMService, agent runtime, tools, workflow graphs
- **LLMService** — Unified entry point for all AI calls with generate/generate_structured/generate_streaming
- **Provider System** — MimoProvider (production), OpenAIProvider (stub), LocalLLMProvider (stub)
- **Agent Runtime** — AgentState, AgentExecutor, AgentRegistry, GraphBuilder (LangGraph)
- **Tool System** — 10 domain tools wrapping existing services
- **Workflow Graphs** — JobProcessingGraph, CompanyProcessingGraph, InsightsGenerationGraph
- **AI Tests** — 70 tests covering providers, agents, tools, workflows, service
- **Async Resume/Cover Generation** — Background processing with WebSocket progress bars
- **Company Context Enrichment** — Resume/cover prompts enriched with linked company intelligence
- **Generation Progress Tracking** — Step-by-step progress with cancel/retry support
- **Generation History** — Resume/cover generations appear in unified history with session_id

### Changed
- **Python 3.14** — Upgraded from 3.15 for stable langgraph compatibility
- **All AI calls via LLMService** — 15 direct MimoRunner/subprocess calls migrated
- **WebSocket for generation progress** — Replaced polling with real-time updates
- **GitHub Actions** — Updated to Python 3.14

### Fixed
- **sqlite3.Row .get() error** — Generation worker properly converts rows to dicts
- **Double pid prefix** — Removed gen_type prefix from pid since prompts add it
- **Curly braces in prompts** — Escaped JSON content in company context for template.format()

## [2.1.0] — 2026-07-25

### Added
- **TypeScript Conversion** — All 68 frontend files converted from JS/JSX to TS/TSX
- **Feature-Based Frontend Architecture** — `features/{jobs,companies,insights,skills,resume,rules}`, `shared/`, `layout/`
- **Skills as Top-Level Tab** — Independent from Insights, own `useSkills` hook and `SkillsTab` component
- **Generation History Drawer** — Unified history across career-intel, roadmaps, job processing, company processing
- **Version Tracking** — `version` column on `pending_jobs`, `pending_companies` for retry counting
- **Font Size System** — Custom Tailwind tokens `text-3xs` (6px) and `text-2xs` (8px) for consistent dense UI
- **API Documentation** — Swagger UI at `/api/docs/`, ReDoc at `/api/redoc/`, OpenAPI 3.0 spec
- **Stale Run Recovery** — On startup, stuck `processing` jobs marked `failed` with version bump
- **Notes+Links Input** — Both jobs and companies accept multi-source input
- **Skills DB Fill** — AI insights automatically fill extracted skills into tech_stack
- **Comprehensive Documentation** — CONTEXT, DOMAIN, FEATURES, API, DEVELOPMENT, AI_AGENTS, DECISIONS, RUNBOOKS

### Changed
- **Renamed "Career Intel" → "Insights"** — All code, DB references, UI, routes, SocketIO events
- **Feature-based frontend architecture** — `components/` → `features/`, `shared/`, `layout/`
- **Per-section prompts** — `generate_all()` runs each section's dedicated prompt instead of monolithic
- **Session resumption** — Worker passes previous session_id to mimo via `--session` for retry continuity
- **Company scores synced** — Card and drawer now show same Fit/Success/Overall scores
- **Navigation reorganized** — Jobs, Companies, Skills (top-level), Insights (sub-tabs), Settings (Resume, Rules)

### Removed
- **Stale agent docs** — `docs/agent/` directory (session-specific, outdated)
- **career-intel naming** — Replaced with `insights` throughout

## [Previous]

### Added
- **Skill Taxonomy** — 5 categories: Technical, Engineering, Professional, Domain, Career
- **Skill Aliases** — Merge duplicate skills with alias tracking
- **Skill Relationships** — Related, similar, parent, child, alternative links
- **Skill Detail Drawer** — Full skill overview with roadmap, rename, hide, remove
- **Skill Management Endpoints** — hide, restore, rename, delete, merge
- **WebSocket Real-Time Updates** — pending, company, career intelligence, skill roadmap events
- **Career Intelligence System** — 6 sections with per-section generation
- **Company Intelligence** — AI analysis with Fit/Success/Overall scoring
- **Processing Queue** — Persistent queue with concurrent workers
- **Scoring Rules** — Configurable rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING)
