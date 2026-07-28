# Microservice Evolution Strategy

## Current State

Modular monolith with 8 bounded contexts, each with clear domain boundaries.

## Future Extraction Path

### Phase 1: Extract AI Context (Lowest Risk)
- Stateless — no database ownership
- Just isolate LLM calls behind an API
- All contexts already depend on `app/ai/`

### Phase 2: Extract Resume Context
- Small, focused — `resumes` table only
- Clear input/output (job data → resume content)
- Event-driven: `ResumeRequested` → `ResumeGenerated`

### Phase 3: Extract Skills Context
- Self-contained — `skills`, `skill_*`, `tech_learning` tables
- No FK dependencies on other contexts
- API: CRUD + roadmap generation

### Phase 4: Extract Career Context
- Depends on reading jobs, companies, skills data
- Would need event subscriptions or API calls to other services
- `career_insights`, `career_insight_runs`, `preferences` tables

### Phase 5: Extract Companies + Jobs
- Tightly coupled via `company_id` FK
- Extract together or break the FK reference
- Most complex — many cross-context dependencies

## Database Ownership

Each extracted service would own its PostgreSQL schema:
- `jobs_service` → `jobs`, `summaries`
- `companies_service` → `companies`, `company_*`
- `skills_service` → `skills`, `skill_*`, `tech_learning`
- `career_service` → `career_insights`, `career_insight_runs`, `preferences`
- `resume_service` → `resumes`, `pending_generations`

## Cross-Service Communication

- **Synchronous**: HTTP/gRPC for real-time queries
- **Asynchronous**: Message queue for events (`JobCreated`, `CompanyAnalyzed`)
- **Shared data**: Event sourcing for data replication
