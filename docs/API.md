# API Reference

## Overview

REST API served by FastAPI on port 5000. All endpoints return JSON. WebSocket (SocketIO, ASGI mode) for real-time updates.

**Base URL**: `http://localhost:5000`
**API Docs**: Swagger UI at `/api/docs/`, ReDoc at `/api/redoc/`

## Authentication

None. All endpoints are publicly accessible.

## Jobs

### GET /api/jobs
Get paginated job list with filtering and sorting.

**Query params**: `offset`, `limit`, `sort_by` (created_at|overall_score|fit_score|success_score|num|company|location), `sort_dir` (asc|desc), `filter_tech`, `filter_cities`, `filter_companies`, `filter_matches`, `filter_work_types`, `filter_employment_types`, `filter_response_status`, `filter_scores`, `filter_applied`

**Response**: `{ jobs: [...], total: number, agg: {...} }`

### GET /api/jobs/:num
Get single job details.

### PUT /api/jobs/:num
Update job fields.

### DELETE /api/jobs/:num
Hard delete job and related data.

### POST /api/jobs/:num/requeue
Re-queue a processed job for reprocessing.

### POST /api/jobs/:num/rescore
Rescore an existing job without re-fetching.

## Companies

### GET /api/companies
Get all processed companies with intelligence scores.

### POST /api/companies
Add a company for research.
**Body**: `{ notes: [{type, content}], links: [{url, title}], source: 'web' }`

### GET /api/companies/:id
Get company details with full intelligence.

### DELETE /api/companies/:id
Delete company and all intelligence data.

## Processing Queue

### GET /api/pending
Get all pending/processing jobs.

### POST /api/pending
Add a job URL (with optional notes+links) to the processing queue.
**Body**: `{ url: string, notes?: [{type, content}], links?: [{url, title}], source?: string }`

### POST /api/pending/:id/process
Start processing a queued job.

### PUT /api/pending/:id/reset
Reset a job to pending state (increments version).

### DELETE /api/pending/:id
Remove a job from the queue.

## Skills

### GET /api/tech-stack
Get visible skills with aliases and tags.
**Query**: `?category=technical|engineering|professional|domain|career`

### POST /api/tech-stack
Create a custom skill.
**Body**: `{ name, level, category, source }`

### PUT /api/tech-stack/:id
Update a skill.

### PATCH /api/tech-stack/:id/rename
Rename a skill (cascades to roadmaps, progress, aliases).

### PATCH /api/tech-stack/:id/hide
Soft-delete (set hidden=1).

### PATCH /api/tech-stack/:id/restore
Restore hidden skill (set hidden=0).

### DELETE /api/tech-stack/:id
Permanently delete skill and aliases.

### POST /api/tech-stack/merge
Merge source skills into target.
**Body**: `{ target_id, source_ids }`

### GET /api/tech-stack/hidden
List hidden skills.

## Skill Roadmaps

### GET /api/skill-roadmaps?skill=X
Get roadmap tree for a skill.

### POST /api/skill-roadmaps/generate
Start AI roadmap generation.
**Body**: `{ skill_name }`

### POST /api/skill-roadmaps/extend
Extend an existing roadmap.

### POST /api/skill-roadmaps/finegrain
Fine-grain roadmap items.

### GET /api/skill-roadmap-progress/all
Get progress summary for ALL skills.

### GET /api/skill-roadmap-progress?skill=X
Get progress for a specific skill.

### PUT /api/skill-roadmap-progress/:id
Toggle item completion.

## Insights

### GET /api/insights
Get all latest intelligence sections.

### GET /api/insights/:section
Get a specific section (overview|opportunities|companies|market|networking|skills_intel).

### POST /api/insights/refresh
Generate ALL insight sections in background.

### POST /api/insights/:section/refresh
Generate a single section in background.

### GET /api/insights/progress
Get current generation progress.

### GET /api/insights/status
Get per-section generation status with lastRun timestamps.

### GET /api/insights/skills-intel
Get latest Skills Intelligence Report.

### POST /api/insights/skills-intel/refresh
Generate Skills Intelligence Report.

### POST /api/insights/cancel
Cancel running analysis.

## Resumes

### GET /api/resumes
Get all resumes.

## System

### GET /api/generation-history
Unified generation history across all subsystems.

### GET /api/rules
Get scoring rules configuration.

## WebSocket Events

| Event | Direction | Room | Purpose |
|-------|-----------|------|---------|
| `pending:update` | Server→Client | — | Job step progress |
| `pending:log` | Server→Client | — | Job processing logs |
| `pending:complete` | Server→Client | — | Job finished |
| `company:update` | Server→Client | — | Company processing progress |
| `insights:progress` | Server→Client | insights | Insights generation progress |
| `skill_roadmap:update` | Server→Client | skills | Per-skill roadmap generation |

## Error Handling

All errors return JSON: `{ error: "<message>" }` with appropriate HTTP status (400, 404, 409, 500).

## Versioning

No API versioning. Breaking changes are avoided by maintaining backward compatibility.
