# Domain Knowledge

## Core Entities

### Job
- **What**: A job posting discovered from LinkedIn, job boards, or manual submission
- **Key fields**: `num` (unique ID), `company`, `role`, `location`, `stack`, `visa`, `overall_score`, `favorite`
- **Scoring**: `fit_score` (0-100) + `success_score` (0-100) = `overall_score` (weighted 0.6/0.4)
- **States**: pending → queued → processing → done/failed
- **Favorite**: a user-managed bookmark flag (`favorite` integer, 0/1) to mark jobs worth pursuing; it is independent of the analysis pipeline and is toggled only through `PUT /api/jobs/{job_id}/favorite`

### JobAnalysis
- **What**: Canonical AI analysis of a single job, produced by the v2 processing pipeline's single combined `job.analyze` LLM call
- **Storage**: `job_analysis` table, one row per `job_id` (unique), upserted on every analysis
- **Key fields**: `payload` (JSON: fields, scores_explanation, summary, skills, insights), `fit_score`, `success_score`, `overall_score`, `recommendation` (apply/consider/skip), `apply_reason`, `summary`, `prompt_version`, `schema_version`, `generated_at`
- **Scoring rules**: deterministic — `overall = round(fit × 0.6 + success × 0.4)`; recommendation from overall: `apply ≥ 80`, `consider ≥ 60`, else `skip`; scores clamped to 0-100
- **Skills**: each required skill tagged `matched` / `missing` / `low` relative to the user profile, with level, category, and evidence
- **Lifecycle**: created only by the analysis phase; hard-deleted together with the job (`DELETE` on the job cascades by repository)
- **Legacy rows**: jobs processed before the analysis phase existed expose an `analysis` block built from the legacy `jobs`/`summaries` projections (no recommendation, grade-derived summary)

### Company
- **What**: A company profile with intelligence analysis
- **Key fields**: `name`, `industry`, `company_type` (Product/Recruiting), `tech_stack`, `funding_stage`
- **Intelligence**: Stored in `company_intelligence` table — overview, culture, visa, career, benefits, technology analysis + scores
- **Scores**: `company_fit_score`, `company_success_score`, `company_overall_score` (A++ to D)

### Skill
- **What**: A skill tracked in the candidate's profile
- **Categories**: Technical, Engineering, Professional, Domain, Career
- **Key fields**: `name`, `level` (1-5), `category`, `confidence`, `market_relevance`
- **Aliases**: Merged skills (e.g., Postgres → PostgreSQL) stored in `skill_aliases`
- **Roadmaps**: Hierarchical learning trees in `skill_roadmaps` with progress tracking

### Resume
- **What**: Generated resume or cover letter
- **Types**: `original`, `original_1`, `linkedin_*`, `resume_*`, `cover_*`
- **Storage**: Content in `resumes.content`, raw text in `resumes.raw_text`
- **Master resume**: uploaded via `POST /api/resumes`, stored as `original_N` with version `N` auto-incremented
- **LinkedIn profile**: uploaded via `POST /api/linkedin`, stored as `linkedin_N` with version auto-incremented
- **PII**: `raw_text` is PII-masked (name line, phone, email, LinkedIn/GitHub URLs) at save time
- **Latest**: the row with the highest `version` for the `original_*` / `linkedin_*` prefix

### Generation
- **What**: A resume or cover letter generation request
- **Key fields**: `job_num`, `type` (resume/cover), `status`, `session_id`
- **States**: queued → processing → done/failed/cancelled

## Business Rules

### Scoring System
- **SHARED rules**: Apply to all entities (visa probability, communication fit)
- **JOB rules**: Job-specific scoring (fit_score, success_score)
- **COMPANY_PRODUCT rules**: Product company scoring
- **COMPANY_RECRUITING rules**: Recruiting agency scoring
- **Formula**: `overall_score = fit_score × 0.6 + success_score × 0.4`

### Visa Assessment
- **BEST**: Confirmed sponsorship, English-first, international team
- **Strong**: Likely sponsorship, international presence
- **Good**: Possible sponsorship, English environment
- **Moderate**: Unclear, may require local authorization
- **Uncertain**: No visa signals found

### Processing Pipeline
1. **Fetch**: Download URL content (supports notes+links for multi-source)
2. **Validate**: Verify it's a real job posting
3. **Extract**: Parse structured fields (title, company, role, stack, etc.)
4. **Score**: Apply scoring rules, calculate fit/success/overall
5. **Save**: Write to DB with deduplication check

### Job Processing Pipeline (v2, SSE)
Runs as a single `ProcessingExecution` (`JOB_PROCESSING`) driven by the runner
over two LangGraph phases:

**Phase 1 — Context Preparation (no LLM)**
1. `load_job` → `collect_sources` → `fetch_sources` → `extract_content` → `build_context` → `validate_context`
2. `persist_context`: writes the combined text to the job row (`raw_description` + `description`) so the analysis phase has a durable LLM input
3. `context_ready` / `execution_failed`

**Phase 2 — Job Analysis (one LLM call)**
1. `load_context` (read prepared content) → `prepare_profile` (skills, latest resume + LinkedIn, scoring rules)
2. `analyze`: single `job.analyze` call via `LLMService.generate_structured` (only provider entry point); the prompt carries the latest resume and LinkedIn as labeled profile-documents sections — the resume is authoritative for skills/seniority, LinkedIn supplements it
3. `extract_skills` (normalize + tag matched/missing/low) → `score` (deterministic overall/recommendation) → `recommend` → `summarize`
4. `persist`: update the jobs row projection + summaries row (legacy grade) + `job_analysis` row
5. `analysis_ready` / `execution_failed`

Each step emits SSE `workflow.step.*` events; the frontend refetches the Job
Details on `execution.completed|failed`.

### Resume/Cover Generation Pipeline
1. **Prepare**: Load job data, resume, rules
2. **Context**: Load company intelligence (if linked)
3. **Generate**: Call LLMService with enriched prompt
4. **Save**: Write to resumes table
5. **Done**: Mark complete, emit WebSocket event

## Domain Workflows

### Job Application Flow
```
URL submitted → queued → fetching → validating → extracting → scoring → saved
```

### Company Research Flow
```
Notes/Links added → queued → fetching → extracting → analyzing → saved
```

### Career Intelligence Flow
```
Generate All → overview → opportunities → companies → market → networking → skills_intel
```

### Resume/Cover Generation Flow
```
Click Generate → pending_generations → prepare → context → generate → save → done
```
