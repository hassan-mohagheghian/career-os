# Features

## Job Processing

**Goal**: Automatically discover, fetch, analyze, and score job postings.

- URL submission with notes+links support
- Real-time WebSocket progress (step-by-step updates)
- Configurable scoring rules (SHARED, JOB, COMPANY_PRODUCT, COMPANY_RECRUITING)
- Version tracking for retries
- Deduplication check (URL-based)
- Bulk operations: rescore-all, reprocess-all

**Components**: `JobsPage`, `JobDrawer`, `ProcessingItem`, `ProcessedCards`
**API**: `POST /api/pending`, `GET /api/jobs`, `POST /api/jobs/:num/rescore`
**Status**: Complete

## Company Intelligence

**Goal**: Extract and analyze company profiles for visa and career assessment.

- Multi-source input (notes + URLs + links)
- Product vs Recruiting classification
- Visa friendliness assessment
- Fit/Success/Overall scoring
- Company intelligence tabs: Overview, Culture, Technology, Visa, Career, Benefits

**Components**: `CompaniesPage`, `CompanyDrawer`, `CompanyCard`, `CompanyProcessingItem`
**API**: `POST /api/companies`, `GET /api/companies/:id`
**Status**: Complete

## Skills Management

**Goal**: Track, categorize, and develop the candidate's skill portfolio.

- 5-category taxonomy (Technical, Engineering, Professional, Domain, Career)
- Skill aliases and merge (DnD)
- Custom skill creation
- Hide/restore/delete operations
- Skill relationships (related, similar, parent, child, alternative)
- Checkable learning roadmaps per skill
- AI-powered roadmap generation, extension, fine-graining

**Components**: `SkillsIntelSection`, `SkillDetailDrawer`, `SkillRoadmapDrawer`
**API**: `GET /api/tech-stack`, `POST /api/skill-roadmaps/generate`
**Status**: Complete

## Career Insights

**Goal**: Provide data-driven career intelligence and market analysis.

- Career health score (0-100)
- Per-section generation: Overview, Skills, Opportunities, Companies, Market, Networking
- AI-generated strengths, gaps, learning recommendations
- Market analysis (countries, cities, remote opportunities)
- Networking targets with LinkedIn search queries
- Real-time progress with session tracking and cancellation

**Components**: `InsightsTab`, `OverviewSection`, `OpportunitiesSection`, `CompaniesSection`, `MarketIntelSection`, `NetworkingIntelSection`
**API**: `POST /api/insights/refresh`, `GET /api/insights/:section`
**Status**: Complete

## Resume Generation

**Goal**: Generate tailored resumes and cover letters for specific jobs.

- AI-powered resume tailoring
- Cover letter generation
- LinkedIn profile integration
- Multiple resume versions (original, tailored, cover)

**Components**: `ResumeTab`
**API**: `GET /api/resumes`, `POST /api/jobs/:num/generate-resume`
**Status**: Complete

## Skills Intelligence (AI Analysis)

**Goal**: Analyze skills against job market and generate development strategy.

- Current state analysis (strengths, gaps, maintain)
- Target state analysis
- Gap analysis with priority scoring
- ROI-based skill scoring
- Learning roadmap (NOW/NEXT/LATER)
- Career readiness score (0-100)
- Fills extracted skills into tech_stack DB

**Components**: `SkillsIntelSection` (under Insights)
**API**: `POST /api/insights/skills-intel/refresh`
**Status**: Complete
