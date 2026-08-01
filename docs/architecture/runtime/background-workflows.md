# Background Workflow Execution

## Purpose

This document describes how long-running workflows are executed inside the runtime architecture.

The background workflow system is responsible for coordinating:

- Background task execution
- Workflow orchestration
- State management
- Progress reporting
- Failure recovery

The execution model separates:

- Task execution
- Workflow execution
- Domain state

---

# Workflow Execution Architecture

The runtime flow:

API Request

↓

ProcessingExecution Created

↓

TaskIQ Task Dispatched

↓

TaskIQ Worker Starts

↓

LangGraph Workflow Executes

↓

Execution State Updated

↓

Progress Events Published

---

# Execution Responsibilities

## TaskIQ Responsibility

TaskIQ is responsible for:

- Starting background execution
- Worker management
- Retry handling
- Task scheduling

TaskIQ does not manage workflow state.

---

## LangGraph Responsibility

LangGraph is responsible for:

- Workflow graph execution
- Node orchestration
- State transitions
- Checkpointing
- Recovery
- Human or external interruptions

LangGraph is the workflow engine.

---

# Workflow Lifecycle

A workflow execution has the following lifecycle:

Created

↓

Queued

↓

Running

↓

Processing Nodes

↓

Completed

or

Failed

The lifecycle state is stored through ProcessingExecution.

---

# Workflow State

Workflow state belongs to LangGraph.

The state contains:

- Current workflow position
- Intermediate results
- Node outputs
- External tool responses
- LLM responses
- Error information

State persistence is handled by LangGraph checkpointing.

---

# Workflow Example

Job processing workflow:

Input URL

↓

Fetch Content

↓

Extract Data

↓

Analyze Content

↓

Send Data To LLM

↓

Generate Score

↓

Generate Career Guidance

↓

Persist Result

Each step is represented as a workflow node.

---

# Progress Reporting

Workflow progress is exposed through processing events.

Events are generated from workflow execution.

Examples:

- WorkflowStarted
- NodeStarted
- NodeCompleted
- WorkflowCompleted
- WorkflowFailed

The frontend consumes progress updates through SSE.

---

# Failure Recovery

Workflow failures are handled independently from task failures.

Task failure examples:

- Worker crash
- Redis unavailable
- Temporary infrastructure failure

Handled by:

- TaskIQ retries

Workflow failure examples:

- LLM failure
- Invalid workflow state
- Node execution failure

Handled by:

- LangGraph checkpoints
- Workflow recovery mechanisms

---

# Scaling

Workflow execution can scale horizontally.

Scaling components:

- API instances
- TaskIQ workers
- Workflow executions

Workers are stateless.

State is persisted externally.

---

# Runtime Dependencies

Workflow execution depends on:

- PostgreSQL
- Redis
- TaskIQ
- LangGraph
- LLM Providers

---

# Deprecated Architecture

Previous:

ARQ Worker

↓

Background Processing

↓

Manual Workflow Execution

Current:

TaskIQ Worker

↓

LangGraph Workflow

↓

Persistent Workflow State

---

# Related Documents

- docs/architecture/runtime/background-service.md
- docs/queue/processing/taskiq-processing.md
- docs/domain/processing/processing-execution.md
- docs/ai/langgraph-state.md
- docs/ai/workflows.md
- docs/workflows/job-processing.md
