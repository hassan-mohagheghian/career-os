# Context Boundaries

## Bounded Contexts

The system is divided into six bounded contexts, each representing a distinct business capability:

### 1. Jobs
**Responsibility**: Job posting lifecycle — discovery, fetching, analysis, scoring, and storage.

**Core Entities**: `Job`, `Summary`

**Key Behaviors**:
- Fetch job postings from URLs
- Extract structured data from raw descriptions
- Score jobs against candidate profile (fit, success, overall)
- Manage job lifecycle (pending → processing → done)

### 2. Companies
**Responsibility**: Company intelligence — profiling, analysis, scoring, and visa assessment.

**Core Entities**: `Company`, `CompanyLink`, `CompanyIntelligence`

**Key Behaviors**:
- Extract company data from multiple sources
- Generate intelligence analysis (culture, technology, visa, career)
- Score companies (fit, success, overall)
- Manage company links and notes

### 3. Skills
**Responsibility**: Skill management, learning roadmaps, and skill relationships.

**Core Entities**: `Skill`

**Key Behaviors**:
- Track skills with categories, confidence, market relevance
- Generate AI-powered learning roadmaps
- Manage skill aliases and relationships
- Track learning progress

### 4. Career
**Responsibility**: Career intelligence, insights, preferences, and scoring rules.

**Core Entities**: `CareerInsight`, `Preference`

**Key Behaviors**:
- Generate career intelligence reports (overview, opportunities, market, networking)
- Manage scoring rules and preferences
- Track career insight generation runs
- Provide career health scoring

### 5. Resume
**Responsibility**: Resume and cover letter generation.

**Core Entities**: `Resume`

**Key Behaviors**:
- Generate tailored resumes for specific jobs
- Generate cover letters
- Store and manage resume versions
- Link resumes to jobs

### 6. Pending
**Responsibility**: Job and company processing queue management.

**Core Entities**: `PendingJob`

**Key Behaviors**:
- Manage processing queue (pending → queued → processing → done/failed)
- Track step-by-step progress
- Handle cancellation and reset
- Manage generation requests

## Cross-Cutting Concerns (Shared Kernel)

The `shared/` context provides infrastructure and domain primitives used by all bounded contexts:

- **Database**: Session management, SQLAlchemy configuration, base models
- **Process Management**: Process lifecycle, temp files, subprocess management
- **WebSocket**: Real-time event broadcasting
- **Configuration**: App settings, DB paths, queue configuration
- **AI**: LLM provider abstraction, prompt loading
- **Domain Primitives**: Base entity, value object, repository interfaces

## Context Map

```
                    ┌─────────────┐
                    │   Pending   │
                    │  (Queue)    │
                    └──────┬──────┘
                           │ enqueues
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │   Jobs   │ │Companies │ │  Resume  │
        │          │ │          │ │          │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             │  provides  │  provides  │
             ▼            ▼            ▼
        ┌──────────────────────────────────┐
        │            Career                │
        │    (Insights & Intelligence)     │
        └──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │            Skills                │
        │   (Roadmaps & Relationships)     │
        └──────────────────────────────────┘
```

## Integration Patterns

- **Synchronous**: API calls between contexts use repository interfaces
- **Asynchronous**: Workers process jobs/companies in background threads
- **Real-time**: WebSocket broadcasts progress updates
- **Event-driven**: Broadcaster notifies connected clients of state changes
