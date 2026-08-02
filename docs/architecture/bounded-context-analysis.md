# Bounded Context Analysis

> Phase 1 deliverable for DDD Modular Monolith Refactoring

## Executive Summary

The Job Search Intelligence platform is a FastAPI + SQLAlchemy monolith serving as an AI-powered career intelligence system. The backend currently lives in `apps/backend/` with a partial clean architecture (repository pattern, domain interfaces, infrastructure implementations) but mixed concerns across layers. This analysis identifies **8 bounded contexts** and a **shared kernel** to guide the DDD modular monolith restructuring.

---

## 1. Identified Bounded Contexts

### 1.1 Jobs Context
**Responsibility:** Job posting lifecycle — fetching, parsing, scoring, storing, and querying job listings.

**Entities:**
- `Job` (aggregate root) — `jobs` table, PK: `num` (int)
- `Summary` — `summaries` table, PK: `num` (FK to jobs.num)

**Value Objects:**
- `JobScore` (fit_score, success_score, overall_score, letter grade)
- `JobLocation` (city, work_type, employment_type)
- `WorkflowLog` (step tracking entries)

**Domain Services:**
- Score normalization (`normalize_score`, `calculate_overall_score`)
- Job data normalization (location, work_type)
- Date parsing (posted, adv_at, see_at)

**Repository Interfaces:** `IJobRepository`
**Infrastructure:** `JobModel`, `SummaryModel`, `SQLAlchemyJobRepository`, `SQLAlchemySummaryRepository`
**API Endpoints:** `api/v1/jobs.py` — CRUD, rescore, requeue, generate
**Workers:** `services/worker.py` — `process_job()`, `rescore_only()`

---

### 1.2 Companies Context
**Responsibility:** Company profiles, intelligence analysis, and external links.

**Entities:**
- `Company` (aggregate root) — `companies` table, PK: `id` (int)
- `CompanyIntelligence` — `company_intelligence` table, FK: `company_id`
- `CompanyLink` — `company_links` table, FK: `company_id`

**Value Objects:**
- `CompanyData` (name, website, domain, industry, country, city, etc.)
- `IntelligenceAnalysis` (overview, culture, technology, visa, scores, etc.)
- `CompanyType` (PRODUCT_COMPANY, RECRUITING_AGENCY, etc.)

**Domain Services:**
- Company type detection
- Intelligence score calculation

**Repository Interfaces:** `ICompanyRepository`, `ICompanyIntelligenceRepository`, `ICompanyLinkRepository`
**Infrastructure:** `CompanyModel`, `CompanyIntelligenceModel`, `CompanyLinkModel`, SQLAlchemy implementations
**API Endpoints:** `api/v1/companies.py` — CRUD, intelligence, links, notes
**Workers:** `services/company_worker.py` — `process_company()`

---

### 1.3 Skills Context
**Responsibility:** Technical skills taxonomy, aliases, relationships, categories, and skill roadmaps.

**Entities:**
- `Skill` (aggregate root) — `skills` table, PK: `id`
- `SkillAlias` — `skill_aliases` table, FK: `skill_id`
- `SkillRelationship` — `skill_relationships` table
- `SkillRoadmap` — `skill_roadmaps` table (self-referential tree)
- `SkillRoadmapProgress` — `skill_roadmap_progress` table
- `SkillRoadmapJob` — `skill_roadmap_jobs` table

**Value Objects:**
- `SkillMetadata` (confidence, market_relevance, evidence, category)
- `RoadmapItem` (title, description, level, sort_order, version)
- `SkillRelationshipType` (prerequisite, related, alternative)

**Domain Services:**
- Skill name normalization
- Skill merging
- Roadmap tree building

**Repository Interfaces:** `ISkillRepository`, `ISkillAliasRepository`, `ISkillRelationshipRepository`, `ISkillRoadmapRepository`, `ISkillRoadmapProgressRepository`, `ISkillRoadmapJobRepository`, `ITechLearningRepository`
**Infrastructure:** `SkillModel`, `SkillAliasModel`, `SkillRelationshipModel`, `SkillRoadmapModel`, etc., SQLAlchemy implementations
**API Endpoints:** `api/v1/skills.py` — CRUD, merge, hide, categorize, relationships
**Services:** `services/skill_roadmap_service.py` — generate, extend, finegrain

---

### 1.4 Rules Context
**Responsibility:** Scoring rules and configuration.

**Entities:**
- `Rule` (scoring rule) — `rules` table, PK: `id`

**Value Objects:**
- `ScoringRule` (category, rule_type, scope, key, value, priority, score_weight)

**Domain Services:**
- Rule-based scoring evaluation

**Repository Interfaces:** `IRuleRepository`
**Infrastructure:** `RuleModel`, `SQLAlchemyRuleRepository`
**API Endpoints:** `/rules`

---

### 1.5 Resume (part of Jobs Context)
**Responsibility:** Resume and cover letter storage, retrieval, and generation lifecycle.

**Entities:**
- `Resume` — `resumes` table, PK: `id` (string)

**Entity Location:** `jobs/domain/entities/resume.py`
**Repository Interface:** `IResumeRepository` at `jobs/domain/repositories/resume_repository.py`
**Infrastructure:** `ResumeModel`, `SQLAlchemyResumeRepository` at `jobs/infrastructure/`
**API Endpoints:** `/resumes` — CRUD, generation
**Workers:** `process_generation()` at `jobs/infrastructure/workers/generation_worker.py`

---

### 1.6 AI Context
**Responsibility:** LLM provider abstraction, agent orchestration, prompt management.

**Entities:** None (stateless)

**Value Objects:**
- `ProviderConfig` (provider settings)
- `ProviderResponse` (content, metadata)
- `AgentState` (LangGraph state)

**Domain Services:**
- LLM provider selection and factory
- Prompt template loading and rendering

**Interfaces:** `LLMProvider` (ABC), `IProcessManager`, `IBroadcaster`
**Infrastructure:** `LLMService`, provider adapters (mimo, openai, gemini, local, opencode, agy), LangGraph agents
**Location:** `app/ai/` (already separate package)

---

### 1.7 Users/Rules Context
**Responsibility:** User preferences and scoring configuration.

**Entities:**
- `Rule` (scoring rules are the primary entity here)

**Note:** This context is thin. The `Rule` entity serves both user preferences and scoring rules. For now, it stays within Rules Context but is architecturally prepared for user authentication expansion.

**Repository Interfaces:** `IRuleRepository`
**Infrastructure:** `RuleModel`, `SQLAlchemyRuleRepository`
**API Endpoints:** `api/v1/rules.py`

---

### 1.8 Pending (Processing Queue) Context
**Responsibility:** Background job processing queue — job submissions, company submissions, generation requests, pipeline state tracking.

**Entities:**
- `PendingJob` — `pending_jobs` table, PK: `id`
- `PendingCompany` — `pending_companies` table, PK: `id`
- `PendingGeneration` — `pending_generations` table, PK: `id`

**Value Objects:**
- `PipelineStep` (step_fetch, step_analyze, step_resume, step_cover, step_db, step_done)
- `JobStatus` (pending → queued → processing → done/failed/paused)
- `SourceType` (cli, web, reprocess, rescore)

**Domain Services:**
- Queue management (`JobQueueManager`)
- State machine transition validation
- Process lifecycle management

**Repository Interfaces:** `IPendingRepository`, `IPendingGenerationRepository`
**Infrastructure:** `PendingJobModel`, `PendingCompanyModel`, `PendingGenerationModel`, SQLAlchemy implementations
**API Endpoints:** `api/v1/pending.py`, `api/v1/pending_companies.py`
**Core:** `core/queue.py` — `JobQueueManager`

---

### 1.9 Shared Kernel
**Responsibility:** Cross-cutting concerns shared across all bounded contexts.

**Contents:**
- Base `Entity` class (UUID/id, created_at, updated_at)
- Value Object primitives
- Domain Events base class
- Application exceptions (`AppError` hierarchy)
- Repository interfaces (ABCs)
- Logging configuration
- Database session management
- Configuration management

**Current Location:** `domain/repositories/`, `exceptions.py`, `dependencies.py`, `infrastructure/database/sqlalchemy_config.py`

---

## 2. Bounded Context Map

```
                    ┌─────────────┐
                    │  Shared     │
                    │  Kernel     │
                    └──────┬──────┘
                           │
          ┌────────┬───────┼───────┬────────┐
          │        │       │       │        │
    ┌─────▼───┐ ┌──▼───┐ ┌─▼──┐ ┌──▼──┐ ┌──▼────┐
    │  Jobs   │ │ Comp │ │Skil│ │Care │ │Resume │
    │         │ │anies │ │ls  │ │er   │ │       │
    └────┬────┘ └──┬───┘ └─┬──┘ └──┬──┘ └──┬────┘
         │         │       │       │        │
         │         │       │       │        │
    ┌────▼─────────▼───────▼───────▼────────▼────┐
    │              Pending (Queue)                │
    └─────────────────┬──────────────────────────┘
                      │
               ┌──────▼──────┐
               │      AI     │
               │  (External) │
               └─────────────┘
```

### Context Relationships

| Source | Target | Relationship | Type |
|--------|--------|-------------|------|
| Jobs | Companies | `company_id` FK | Partner |
| Jobs | Skills | `stack` field references skills | Consumer |
| Jobs | Resume | `job_num` links resumes | Partner |
| Companies | Skills | Tech stack references | Consumer |
| Career | Jobs | Reads job data for insights | Consumer |
| Career | Companies | Reads company data | Consumer |
| Career | Skills | Reads skill data | Consumer |
| Career | Preferences | Scoring rules | Owner |
| Pending | Jobs | Creates jobs after processing | Partner |
| Pending | Companies | Creates companies | Partner |
| Pending | Resume | Triggers generation | Partner |
| AI | All | LLM services | Infrastructure |

---

## 3. Dependencies

### 3.1 Inbound Dependencies (who depends on this context)
- **Jobs** ← Pending, Career, Resume
- **Companies** ← Jobs, Pending, Career
- **Skills** ← Jobs, Companies, Career
- **Career** ← (standalone, reads from others)
- **Resume** ← Pending, Jobs
- **AI** ← All contexts
- **Pending** ← (standalone, creates into others)
- **Preferences** ← Jobs, Companies (via rules loading)

### 3.2 Outbound Dependencies (what this context depends on)
- **Jobs** → Companies (FK link), Preferences (scoring rules)
- **Companies** → Preferences (scoring rules)
- **Skills** → (none)
- **Career** → Jobs, Companies, Skills (reads for insights), AI
- **Resume** → Jobs, AI
- **Pending** → Jobs, Companies, AI
- **AI** → (none, external LLM APIs)

---

## 4. Communication Between Contexts

### 4.1 Synchronous (within request)
- API endpoints use repository pattern — single DB session per request
- Cross-context reads happen within services (e.g., insights reads jobs data)

### 4.2 Asynchronous (background processing)
- `JobQueueManager` orchestrates pending jobs → triggers `process_job()` or `process_company()`
- Workers use separate DB sessions per step
- WebSocket/SSE broadcasts for real-time progress

### 4.3 Domain Events (future)
- Not yet implemented
- Candidates: `JobCreated`, `JobScored`, `CompanyAnalyzed`, `InsightGenerated`

---

## 5. Future Microservice Extraction Possibility

| Context | Extraction Priority | DB Ownership | Complexity |
|---------|-------------------|--------------|------------|
| AI | High | None (stateless) | Low — just isolate LLM calls |
| Career | Medium | — | Medium — depends on reading other contexts |
| Resume | Medium | `resumes` | Low — small, focused |
| Skills | Medium | `skills`, `skill_*`, `tech_learning` | Medium — self-contained |
| Companies | Low | `companies`, `company_*` | Medium — complex intelligence pipeline |
| Jobs | Low | `jobs`, `summaries` | High — core aggregate, many dependencies |
| Pending | Low | `pending_*` | High — orchestrates everything |
| Rules | None | `rules` | Shared — should stay in shared kernel |

### Database Ownership
- Each context could own its tables in a separate PostgreSQL schema
- `jobs.company_id` FK → would become a cross-service reference (UUID-based)
- `pending_generations.job_num` → would become an event-driven reference

---

## 6. Current Issues to Address

1. **Mixed concerns in `services/`** — Some business logic in API layer, some in services
2. **Global state in `services/insights.py`** — Module-level `_current_run` dict, `_analysis_lock`
3. **Duplicate session management** — Every service function creates its own session
4. **Legacy Flask-compat routes** — `api/router.py` has inline endpoints not in v1 sub-routers
5. **Two parallel service layers** — `services/process/` and top-level `services/*.py`
6. **No domain entities** — All data passes as `dict[str, Any]` through repositories
7. **No use cases** — Business logic directly in worker functions
8. **SQLAlchemy models mixed with domain** — Some queries directly in API handlers
