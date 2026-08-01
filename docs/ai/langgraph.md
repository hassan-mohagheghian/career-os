# LangGraph

## Purpose

This document describes the role of LangGraph in the AI processing architecture.

LangGraph is used as the workflow execution engine for complex AI-driven processing.

It provides:

- Graph-based workflow execution
- State management
- Checkpointing
- Recovery
- Resumable workflows
- Node orchestration

---

# Architecture Position

LangGraph is part of the AI execution layer.

System flow:

API

↓

ProcessingExecution

↓

TaskIQ Task

↓

TaskIQ Worker

↓

LangGraph Workflow

↓

Workflow Nodes

↓

LLM Providers / Tools

---

# Responsibilities

LangGraph is responsible for:

- Executing workflow graphs
- Managing workflow nodes
- Passing state between nodes
- Persisting checkpoints
- Recovering interrupted executions
- Coordinating AI processing steps

LangGraph is not responsible for:

- Queue management
- Background worker lifecycle
- User permissions
- Job lifecycle
- Business entities

---

# Relationship With TaskIQ

TaskIQ starts the workflow execution.

The responsibility boundary:

TaskIQ:

- Receives background tasks
- Runs worker processes
- Handles retries
- Executes application services

LangGraph:

- Runs the workflow
- Executes nodes
- Manages workflow state

Flow:

TaskIQ Worker

↓

Create LangGraph Run

↓

Execute Workflow

↓

Update ProcessingExecution

---

# Relationship With ProcessingExecution

Each LangGraph execution belongs to a ProcessingExecution.

Relationship:

Job

↓

ProcessingExecution

↓

LangGraph Workflow Run

ProcessingExecution stores:

- Execution status
- Job relationship
- Error state
- User-visible lifecycle

LangGraph stores:

- Current node
- Workflow state
- Intermediate data
- Checkpoints

---

# Workflow Graph

A LangGraph workflow is represented as a graph.

A graph contains:

- Nodes
- Edges
- State transitions

Example:

START

↓

Fetch Content

↓

Extract Information

↓

Analyze Data

↓

LLM Processing

↓

Generate Score

↓

Generate Career Guidance

↓

END

---

# State Management

LangGraph state represents temporary workflow execution context.

Example state:

```text
{
  job_data,
  extracted_content,
  analysis_results,
  provider_responses,
  generated_insights,
  current_step
}
```

State is passed between workflow nodes.

State Ownership

Different types of data have different owners.

PostgreSQL

Owns:

Jobs
ProcessingExecutions
Final results
Domain entities
LangGraph State

Owns:

Workflow progress
Intermediate results
Node outputs
Temporary execution context
Redis

Owns:

Task communication
Broker messages
Checkpointing

Checkpointing allows workflows to continue after interruption.

Use cases:

Worker restart
Temporary failures
Long-running workflows
Human interruption
External dependency failure

Checkpoint data allows:

Resume execution
Restore workflow state
Continue from previous node
Recovery Model

Failures are handled at different layers.

TaskIQ Failure

Example:

Worker unavailable
Redis connection failure

Handled by:

TaskIQ retry
Workflow Failure

Example:

LLM provider error
Tool execution failure
Invalid workflow state

Handled by:

LangGraph checkpoint recovery
Domain Failure

Example:

Invalid job information
Business rule violation

Handled by:

Domain layer
Node Design Rules

Workflow nodes should:

Have a single responsibility
Receive state
Update state
Avoid direct infrastructure coupling

A node should not:

Manage queues
Update frontend directly
Control workflow lifecycle manually
Tool Usage

LangGraph nodes can use tools.

Examples:

Web fetching
Data extraction
Search
LLM providers

Tool execution should happen through the application tool layer.

Related:

docs/ai/tooling.md

Progress Events

LangGraph execution generates workflow progress events.

Example:

Node Started

↓

Workflow Event

↓

Processing Event

↓

SSE Stream

↓

Frontend

Related:

docs/api/sse/processing-events.md

Persistence

LangGraph persistence is separate from domain persistence.

Workflow state:

LangGraph checkpoint storage

Business state:

PostgreSQL

The system must not store workflow state directly inside domain entities.

Testing

LangGraph workflows should be tested independently.

Tests should verify:

Node behavior
State transitions
Failure recovery
Checkpoint restoration
Workflow completion
Related Documents
docs/ai/workflows.md
docs/ai/langgraph-state.md
docs/domain/processing/processing-execution.md
docs/domain/processing/events.md
docs/architecture/runtime/background-service.md
docs/queue/processing/taskiq-processing.md
