# Project Context

## What This Project Solves

Job Search Intelligence is an AI-powered career platform that helps software engineers find and apply for jobs, especially visa-sponsored roles in Europe (Germany, Netherlands). It automates the job search workflow: discovering jobs, analyzing companies, managing skills, generating resumes, and providing career insights.

## Target Users

- Software engineers seeking visa-sponsored positions in Europe
- Career changers who need data-driven skill gap analysis
- Job seekers who want automated resume tailoring

## Core Concepts

- **Job Processing Pipeline**: URL → fetch → extract → AI analysis → score → save
- **Company Intelligence**: Profile extraction, visa assessment, Fit/Success/Overall scoring
- **Skills Management**: 5-category taxonomy, AI-powered insights, learning roadmaps
- **Career Insights**: Health score, market analysis, opportunity funnel
- **Resume Generation**: AI-tailored resumes and cover letters with real-time progress

## Key Rules

1. **Provider abstraction**: All AI calls go through LLMService — never call providers directly. Default provider is Mimo CLI, but OpenAI and local LLMs are supported via `AI_PROVIDER` env var
2. **TypeScript frontend**: All client code is `.ts`/`.tsx`
3. **SQLAlchemy ORM**: Use SQLAlchemy for all database access, never raw SQL
4. **Feature-based architecture**: Frontend organized by `features/`, `shared/`, `layout/`
5. **Single generation lock**: Only one AI analysis runs at a time
6. **URL uniqueness**: Base URL without query params for deduplication
7. **Hard delete for processed jobs**: `DELETE FROM jobs` + related tables
8. **All cards must have delete button**
9. **Default sort**: Newest first (`created_at desc`)
10. **Save folder paths configurable via .env**
11. **DDD/SOLID/TDD**: Follow domain-driven design, SOLID principles, and test-driven development

## System Boundaries

- **In scope**: Job discovery, company analysis, skill management, resume generation, career insights
- **Out of scope**: Job application submission, interview scheduling, salary negotiation
- **External integrations**: AI Agent Layer (LLMService + provider abstraction), LinkedIn (scraping), job boards (URL fetching)
