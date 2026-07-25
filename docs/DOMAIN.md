# Domain Knowledge

## Core Entities

### Job
- **What**: A job posting discovered from LinkedIn, job boards, or manual submission
- **Key fields**: `num` (unique ID), `company`, `role`, `location`, `stack`, `visa`, `overall_score`
- **Scoring**: `fit_score` (0-100) + `success_score` (0-100) = `overall_score` (weighted 0.6/0.4)
- **States**: pending → queued → processing → done/failed

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
