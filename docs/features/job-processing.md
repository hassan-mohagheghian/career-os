# Job Processing

## Purpose

The Job Processing feature transforms an imported job into structured, searchable, and scored data.

It is the core AI workflow of the system.

A ProcessingExecution is created whenever the user requests processing for a job.

The execution runs asynchronously through ARQ and LangChain and streams live progress to the frontend using Server-Sent Events (SSE).

---

# Goals

The feature must:

- Process imported jobs asynchronously.
- Produce structured job information.
- Calculate AI scores.
- Generate recommendations.
- Persist all generated data.
- Stream execution progress to the frontend.
- Allow future workflow extensions without changing the execution model.

---

# Scope

Current implementation includes:

- Job Processing
- ProcessingExecution lifecycle
- LangChain workflow
- Scoring
- Recommendation generation
- Live progress updates
- Background execution
- Result persistence

---

# Out of Scope

The following features are intentionally excluded from the current implementation:

- Company processing
- Company intelligence
- Insight generation
- Cover letter generation
- Resume generation
- CV optimization
- Interview preparation
- Multi-agent collaboration

These features will be implemented as independent ProcessingExecution types in the future.

---

# Processing Flow

User clicks Process

↓

ProcessingExecution is created

↓

Execution is queued

↓

Worker starts execution

↓

LangChain workflow executes

↓

Results are stored

↓

Execution completes

↓

Frontend updates automatically through SSE

---

# Dependencies

This feature depends on:

- Processing bounded context
- AI bounded context
- ARQ
- LangChain
- Prompt Registry
- Rule Engine
- LLM Configuration
- Server-Sent Events

---

# Acceptance Criteria

A successful implementation must satisfy all of the following:

- Processing never blocks HTTP requests.
- Every execution has a unique UUIDv7.
- Progress is streamed in real time.
- Processing is observable.
- Results are persisted.
- Failures are recoverable.
- The workflow is resumable.
- Future execution types can reuse the same infrastructure.

---

# Future Extensions

The ProcessingExecution infrastructure is designed to support additional execution types, including:

- Company Processing
- Cover Letter Generation
- Resume Generation
- Resume Optimization
- Company Analysis
- Market Analysis
- Career Insights

No architectural changes should be required when introducing new execution types.
