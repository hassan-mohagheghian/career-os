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
- **Scores**: `visa_score`, `tech_match`, `career_score`, `priority` (A++ to D)

### Skill (Tech Stack)
- **What**: A skill tracked in the candidate's profile
- **Categories**: Technical, Engineering, Professional, Domain, Career
- **Key fields**: `name`, `level` (1-5), `category`, `confidence`, `market_relevance`
- **Aliases**: Merged skills (e.g., Postgres → PostgreSQL) stored in `skill_aliases`
- **Roadmaps**: Hierarchical learning trees in `skill_roadmaps` with progress tracking

### Resume
- **What**: Generated resume or cover letter
- **Types**: `original`, `original_1`, `linkedin_*`, `tailored_*`, `cover_*`
- **Storage**: Content in `resumes.content`, raw text in `resumes.raw_text`

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

## Domain Workflows

### Job Application Flow
```
URL submitted → queued → fetching → validating → extracting → scoring → saved
                                                                ↓
                                                          Ready to apply
```

### Company Research Flow
```
Notes/Links added → queued → fetching → extracting → analyzing → saved
                                                                ↓
                                                          Intelligence available
```

### Career Intelligence Flow
```
Generate All → overview (parallel) → opportunities → companies → market → networking
                                                                  ↓
                                                           Insights ready
```
