# Prompt 056 - Implement Job Context Preparation Workflow Using LangGraph

## Objective

Implement the first version of the Job Context Preparation Workflow.

The purpose of this workflow is to prepare a complete and validated context for a Job before any LLM-based analysis starts.

This phase must NOT include any LLM calls.

The workflow should only handle:

- Loading Job information
- Collecting Job sources
- Fetching external content
- Extracting clean text
- Combining information into a processing context
- Validating the context
- Preparing the execution for future analysis stages

Expected flow:

Job

↓

Collect Sources

↓

Fetch Content

↓

Extract Content

↓

Build Context

↓

Validate Context

↓

Ready For Analysis

---

# Important Migration Rule

Before implementing this workflow:

Check whether an older Job Processing Workflow has already been implemented.

If an existing workflow exists:

- Remove the old workflow implementation.
- Remove its related tests.
- Remove obsolete nodes.
- Remove obsolete services created only for that workflow.
- Replace it completely with this new design.

Do not keep two different Job Processing workflows.

The new workflow described here becomes the single source of truth.

Future stages such as:

- LLM analysis
- scoring
- career guidance
- recommendations

will be added later as new workflow stages.

---

# Read Documentation First

Before making changes, read:

- docs/adr/019-taskiq-migration.md
- docs/architecture/runtime/background-service.md
- docs/architecture/runtime/background-workflows.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/events.md
- docs/domain/processing/job-state-machine.md
- docs/ai/workflows.md
- docs/ai/langgraph.md
- docs/ai/langgraph-state.md
- docs/queue/processing/taskiq-processing.md

---

# Architecture Rules

Follow the existing Modular Monolith and Bounded Context architecture.

Do not create generic shared services.

Respect these boundaries:

---

## Job Context

Responsible for:

- Job entity
- Job metadata
- Loading Job information
- Job related application services

Examples:

- JobRepository
- JobService

---

## Processing Context

Responsible for:

- ProcessingExecution
- Workflow execution
- LangGraph workflow
- Workflow state
- Context preparation

LangGraph belongs here because it is the workflow orchestration engine.

It is not responsible for AI reasoning at this stage.

---

## Content Infrastructure

Responsible for:

- HTTP fetching
- Browser fetching
- HTML parsing
- Text extraction

These are infrastructure adapters.

They must not leak into domain logic.

Possible implementations can change in the future.

Examples:

Current:

- httpx
- Playwright
- trafilatura

Future:

- Firecrawl
- Jina Reader
- other providers

The workflow should depend on application interfaces, not concrete infrastructure implementations.

---

# Implement Processing State

Create a strongly typed JobProcessingState.

Use:

- Pydantic models
- Type-safe definitions

The state should contain:

- execution_id
- job_id
- job data
- sources
- fetched contents
- extracted contents
- notes
- processing context
- validation result
- errors
- execution status

---

# Implement LangGraph Workflow

Create:

JobContextPreparationGraph

The graph should contain these nodes:

## 1. LoadJobNode

Responsibilities:

- Load Job information
- Populate initial workflow state

Use:

- JobService
- JobRepository

Do not access the database directly from the node.

---

## 2. CollectSourcesNode

Responsibilities:

Collect all available sources:

- Primary Job URL
- Additional URLs
- Job notes

Normalize them into Source models.

Example:

```text
Source

- url
- type
- metadata
```

3. FetchSourcesNode

Responsibilities:

Fetch all external sources.

Create a ContentFetcher abstraction.

Requirements:

Support multiple URLs.
Handle individual failures.
One failed source must not fail the entire workflow.

Preferred implementations:

Primary:

httpx

Fallback:

Playwright 4. ExtractContentNode

Responsibilities:

Convert fetched data into clean text.

Create ContentExtractor abstraction.

Preferred tools:

Primary:

trafilatura

Fallback:

BeautifulSoup
readability-lxml

Output:

Structured extracted content.

5. BuildContextNode

Responsibilities:

Create the final JobProcessingContext.

The context should include:

Job information
Extracted content
Notes
Source metadata

This object will later become the input for:

LLM analysis
scoring
career guidance

Do not add those stages now.

6. ValidateContextNode

Responsibilities:

Validate that enough information exists.

Examples:

Invalid:

no extracted content
empty notes
no usable source

Valid:

at least one meaningful content source exists

Create conditional edges:

Valid:

ContextReady

Invalid:

ExecutionFailed
Application Services

Create application services where needed:

Example:

application/
processing/
services/
context-builder
context-validator

Nodes should orchestrate services.

Nodes should not contain business logic.

Infrastructure Services

Create infrastructure adapters:

Example:

infrastructure/
content/
fetchers/
httpx-fetcher
playwright-fetcher

        extractors/
            trafilatura-extractor
            bs4-extractor

TaskIQ Integration

TaskIQ is only responsible for background execution.

Create task:

process_job_context_task(execution_id)

The task should:

Load ProcessingExecution
Create initial workflow state
Execute LangGraph workflow
Update ProcessingExecution status
Emit processing events

TaskIQ must not contain workflow logic.

Events

Emit events:

processing.started

processing.loading_job

processing.fetching_sources

processing.extracting_content

processing.context_ready

processing.failed

These events will later be consumed by:

SSE API
Frontend workflow visualization
Testing Requirements

Implement tests for:

State
state creation
state transitions
Nodes
LoadJobNode
CollectSourcesNode
FetchSourcesNode
ExtractContentNode
BuildContextNode
ValidateContextNode
Workflow

Test:

successful workflow execution
failed source handling
empty context handling
invalid context handling

Remove all tests related to the previous Job Processing Workflow if they exist.

Expected Final Architecture
FastAPI

↓

ProcessingExecution

↓

TaskIQ Task

↓

LangGraph JobContextPreparationGraph

↓

Workflow Nodes

↓

Application Services

↓

Infrastructure Adapters

↓

JobProcessingContext

↓

Ready For Future LLM Analysis

No LLM integration should exist in this implementation.
