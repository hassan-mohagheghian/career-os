# ADR-019: Replace ARQ with TaskIQ for Background Task Execution

## Status

Accepted

## Date

2026-08-01

## Context

The system currently uses ARQ as the background task execution mechanism for processing long-running jobs.

The current architecture contains:

- FastAPI API layer
- Background processing workers
- ProcessingExecution domain service
- LangGraph-based workflow execution
- Redis-based queue infrastructure
- Real-time progress delivery through SSE

The system needs a reliable background execution layer for:

- Job processing
- AI workflow execution
- URL fetching and extraction
- LLM provider calls
- Scoring pipelines
- Retry handling
- Long-running workflow execution

ARQ was initially selected because it provides a simple Redis-based async task queue.

However, the project requirements have evolved:

- The system requires a more extensible task execution layer.
- Background execution should be separated from workflow orchestration.
- LangGraph should own workflow state and execution logic.
- Queue implementation should remain an infrastructure concern.
- Future scaling may require additional broker capabilities.

## Decision

Replace ARQ with TaskIQ as the background task execution framework.

TaskIQ becomes the infrastructure layer responsible for:

- Dispatching background tasks
- Managing workers
- Handling retries
- Executing scheduled tasks
- Communicating with Redis broker

TaskIQ does not own business workflow logic.

Workflow execution remains inside the application layer through LangGraph.

The new architecture:
