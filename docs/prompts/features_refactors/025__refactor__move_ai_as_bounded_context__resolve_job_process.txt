# ROLE

You are a Principal AI Architect, Software Architect, and Senior Backend Engineer.

You specialize in:

- LangGraph
- LangChain
- AI Workflow Orchestration
- FastAPI
- Domain Driven Design
- Hexagonal Architecture
- Clean Architecture
- Event-driven systems
- Multi-provider LLM platforms

Your task is to redesign the AI processing architecture of an existing career intelligence platform.

This is not a simple refactor.

This is a complete redesign of the AI orchestration layer while preserving existing business capabilities.

--------------------------------------------------
PROJECT CONTEXT
--------------------------------------------------

[PASTE CURRENT PROJECT CONTEXT HERE]

--------------------------------------------------
CURRENT STATE
--------------------------------------------------

The backend has already been refactored into DDD bounded contexts.

Examples:

- jobs
- companies
- skills
- career
- users
- shared

There is also an AI application responsible for:

- prompt execution
- provider abstraction
- workflow execution

Currently AI processing is mostly procedural.

The goal is to redesign it using LangGraph.

--------------------------------------------------
MAIN OBJECTIVE
--------------------------------------------------

Design a reusable AI workflow platform.

Every business workflow should become a graph.

Examples:

Job Processing Graph

Company Processing Graph

Skill Extraction Graph

Resume Generation Graph

Insight Generation Graph

Roadmap Generation Graph

The platform should support future workflows without architectural changes.

--------------------------------------------------
AI BOUNDED CONTEXT
--------------------------------------------------

Analyze whether the current AI application should become a bounded context inside the backend.

If appropriate:

Move it under:

app/

    ai/

        domain/

        application/

        infrastructure/

        presentation/

The AI context should own:

- Providers
- Prompt templates
- Graph definitions
- Tool registration
- Output parsing
- Execution engine

Business contexts should not directly use LangChain or LangGraph.

They communicate only through AI Application interfaces.

--------------------------------------------------
PROVIDER ARCHITECTURE
--------------------------------------------------

Design a provider abstraction.

Support:

- OpenAI
- OpenRouter
- Anthropic
- Google Gemini
- Local models

Business code must never depend on provider SDKs.

Providers should be replaceable through configuration.

--------------------------------------------------
JOB PROCESSING GRAPH
--------------------------------------------------

Redesign the entire Job Processing pipeline.

The workflow starts with:

User submits:

Required:

- at least one job source

Optional:

- additional links
- notes

Validation rules:

If at least one job source is successfully extracted:

continue

If all URLs fail but one note contains a complete job description:

continue

If all URLs fail and no usable notes exist:

return validation error

The graph should automatically decide which source to trust.

--------------------------------------------------
JOB GRAPH STAGES
--------------------------------------------------

Design explicit graph nodes.

Suggested stages:

1.

Input Validation

↓

2.

URL Fetching

↓

3.

Fallback to Notes

↓

4.

Raw Content Extraction

↓

5.

Content Cleaning

↓

6.

Structured Extraction

↓

7.

Job Analysis

↓

8.

Skill Extraction

↓

9.

Scoring

- Fit Score
- Success Score

↓

10.

Summary Generation

↓

11.

Persistence

↓

12.

Completion Event

Each node should have:

- inputs
- outputs
- retry strategy
- failure handling

--------------------------------------------------
GRAPH FEATURES
--------------------------------------------------

Support:

retry

conditional branches

parallel execution

human approval (future)

checkpointing

resumability

partial success

streaming progress

--------------------------------------------------
PROGRESS REPORTING
--------------------------------------------------

Every node should emit progress events.

Backend:

WebSocket

↓

Frontend

The user should always see:

Current stage

Completed stages

Failed stages

Estimated remaining work

Messages should survive:

page refresh

temporary disconnect

browser restart

--------------------------------------------------
GENERATION HISTORY
--------------------------------------------------

Every execution should create a Generation Session.

Track:

Session ID

Workflow Type

Started At

Completed At

Current Stage

Status

Progress

Errors

Associated Entity

Example:

Job

Company

Resume

Roadmap

Generation history should survive server restarts.

--------------------------------------------------
GRAPH STATE STORAGE
--------------------------------------------------

Design state persistence.

Requirements:

Resume execution

Recover after restart

Audit execution

Replay execution

Future distributed execution compatibility

--------------------------------------------------
PROMPT MANAGEMENT
--------------------------------------------------

Every graph node should own its prompts.

Example:

jobs/

    infrastructure/

        ai/

            prompts/

                extract_job.md

                summarize_job.md

                score_job.md

Avoid global prompt folders.

--------------------------------------------------
TOOLS
--------------------------------------------------

Design reusable LangChain tools.

Examples:

FetchURLTool

ExtractHTMLTool

ExtractPDFTool

ExtractSkillsTool

CompanyLookupTool

DuplicateDetectionTool

Every tool must be independently testable.

--------------------------------------------------
OUTPUT PARSING
--------------------------------------------------

Every AI response should produce structured outputs.

Prefer:

Pydantic models

Structured parsing

Validation

Avoid free-form parsing whenever possible.

--------------------------------------------------
ERROR HANDLING
--------------------------------------------------

Support:

Provider timeout

Rate limits

Invalid outputs

Retry

Fallback providers

Graceful degradation

--------------------------------------------------
TESTING
--------------------------------------------------

Create tests for:

Individual nodes

Entire graphs

Prompt validation

Provider abstraction

Progress events

Failure recovery

Checkpoint restoration

--------------------------------------------------
DOCUMENTATION
--------------------------------------------------

Create or update:

docs/ai/ai-platform.md

docs/ai/langgraph-architecture.md

docs/ai/job-processing-graph.md

docs/ai/provider-abstraction.md

docs/ai/progress-events.md

docs/ai/generation-history.md

docs/architecture/ai-bounded-context.md

docs/adr/005-langgraph-ai-platform.md

--------------------------------------------------
OUTPUT
--------------------------------------------------

Generate:

1. Current AI Architecture Analysis

2. AI Bounded Context Design

3. Provider Architecture

4. LangGraph Platform Architecture

5. Job Processing Graph

6. State Persistence Strategy

7. Progress Event Design

8. WebSocket Event Specification

9. Generation History Design

10. Prompt Organization

11. Testing Strategy

12. Documentation Plan

13. Acceptance Criteria

14. Implementation Checklist

The resulting architecture must become the foundation for every future AI workflow in the platform while remaining fully compatible with DDD, Hexagonal Architecture, and future microservice extraction.
