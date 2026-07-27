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
- URL-addressable skill drawer (`#skills/{skillName}` deep linking)
- Two-tab skill drawer: Details + Roadmap
- Generation history per skill with provider/session tracking
- Action buttons: Regenerate, Extend, Finegrain (inline in drawer)

**Components**: `SkillsIntelSection`, `SkillDetailDrawer`, `SkillRoadmapDrawer` (dashboard recommendations)
**API**: `GET /api/tech-stack`, `POST /api/skill-roadmaps/generate`, `GET /api/skill-roadmaps/jobs`
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

- AI-powered resume tailoring with company context enrichment
- Cover letter generation with company intelligence
- Real-time WebSocket progress bars
- Immediate content display on completion
- LinkedIn profile integration
- Multiple resume versions (original, tailored, cover)
- Generation history with session tracking

**Components**: `ResumeTab`, `DocumentsTab` (in JobDrawer)
**API**: `POST /api/jobs/:num/generate-resume`, `POST /api/jobs/:num/generate-cover`
**Status**: Complete

## Skills Intelligence (AI Analysis)

**Goal**: Analyze skills against job market and generate development strategy.

- Current state analysis (strengths, gaps, maintain)
- Target state analysis
- Gap analysis with priority scoring
- ROI-based skill scoring
- Learning roadmap (NOW/NEXT/LATER)
- Career readiness score (0-100)
- Fills extracted skills into skills DB

**Components**: `SkillsIntelSection` (under Insights)
**API**: `POST /api/insights/skills-intel/refresh`
**Status**: Complete

## AI Agent Orchestration

**Goal**: Flexible multi-provider AI system with provider abstraction.

- LLMService — unified entry point for all AI calls
- Provider abstraction — swap Mimo/OpenAI/Local via env var
- Agent runtime — LangGraph-based workflow orchestration
- Tool system — domain tools wrapping existing services
- Workflow graphs — composable, stateful processing pipelines
- DDD/SOLID/TDD throughout

**Components**: `app/ai/` (providers, agents, tools, runtime, prompts)
**Config**: `AI_PROVIDER=mimo` in `.env`
**Status**: Complete
