# AI Workflows

## Purpose

This document describes the AI workflow architecture.

AI workflows define how complex processing tasks are orchestrated using LangGraph.

A workflow is responsible for coordinating multiple processing steps such as:

- Data fetching
- Content extraction
- Analysis
- LLM execution
- Scoring
- Insight generation

---

# Workflow Architecture

The workflow execution architecture:

API

↓

ProcessingExecution

↓

TaskIQ Background Task

↓

LangGraph Workflow

↓

Workflow Nodes

↓

LLM Providers / Tools

↓

Result

---

# Workflow Engine

LangGraph is the workflow execution engine.

LangGraph provides:

- Graph-based execution
- Node orchestration
- State management
- Checkpointing
- Recovery
- Resumable execution

Workflows should not be implemented as manually chained function calls.

---

# Workflow Responsibilities

A workflow is responsible for:

- Defining execution steps
- Connecting processing nodes
- Managing workflow transitions
- Coordinating tools and providers
- Producing intermediate results

A workflow is not responsible for:

- Queue management
- Worker lifecycle
- User authorization
- Job lifecycle management

---

# Relationship With ProcessingExecution

Each workflow execution belongs to a ProcessingExecution.

Relationship:

Job

|

ProcessingExecution

|

LangGraph Workflow Run

ProcessingExecution manages:

- Execution lifecycle
- User-visible status
- Failure state

LangGraph manages:

- Workflow state
- Node execution
- Checkpoints

---

# Workflow State

Workflow state is owned by LangGraph.

The state contains:

- Current node
- Intermediate results
- Tool outputs
- LLM responses
- Temporary workflow data
- Execution context

Workflow state should not be stored inside Job entities.

---

# Checkpointing

LangGraph checkpoints allow workflows to:

- Resume after failures
- Continue interrupted executions
- Persist intermediate state

Checkpoint data is separate from business data.

Business data:

PostgreSQL

Workflow state:

LangGraph checkpoint storage

---

# Workflow Nodes

A workflow consists of multiple nodes.

Example:

Job URL

↓

Fetch Content Node

↓

Extract Information Node

↓

Analyze Content Node

↓

LLM Analysis Node

↓

Score Generation Node

↓

Career Guidance Node

Each node:

- Receives workflow state
- Performs one responsibility
- Updates workflow state

---

# Job Processing Workflow

Example:

1. Receive Job

2. Fetch external data

3. Extract information

4. Analyze company and role

5. Send context to LLM provider

6. Generate score

7. Generate career guidance

8. Persist final result

---

# Tool Integration

Workflow nodes can use tools.

Examples:

- Web fetching
- Search providers
- Data extraction tools
- LLM providers

Tools are called by workflow nodes.

---

# Failure Handling

Failures can happen at different levels.

## Task Execution Failure

Examples:

- Worker crash
- Redis unavailable

Handled by:

- TaskIQ retry mechanism

## Workflow Failure

Examples:

- Invalid state
- Provider failure
- Node execution error

Handled by:

- LangGraph checkpoints
- Workflow recovery

## Business Failure

Examples:

- Invalid job data
- Missing required information

Handled by:

- Domain validation

---

# Progress Reporting

Workflow progress is exposed through events.

Flow:

LangGraph Node

↓

Workflow Event

↓

Processing Event

↓

SSE

↓

Frontend

Related:

docs/api/sse/processing-events.md

---

# Workflow Lifecycle

Created

↓

Initialized

↓

Running

↓

Checkpointed

↓

Completed

or

Running

↓

Failed

---

# Related Documents

- docs/domain/processing/processing-execution.md
- docs/domain/processing/events.md
- docs/architecture/runtime/background-service.md
- docs/architecture/runtime/background-workflows.md
- docs/queue/processing/taskiq-processing.md
- docs/ai/langgraph.md
- docs/ai/langgraph-state.md
