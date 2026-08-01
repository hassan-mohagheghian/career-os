# LangGraph State Management

## Purpose

This document describes how workflow state is managed inside LangGraph.

LangGraph state represents the temporary execution context required to run an AI workflow.

It is responsible for maintaining information between workflow nodes.

---

# State Architecture

Workflow execution flow:

ProcessingExecution

↓

LangGraph Workflow Run

↓

Workflow State

↓

Checkpoint Storage

The workflow state exists only to support workflow execution.

---

# State Ownership

Different layers own different types of data.

## Domain Layer

Owned by PostgreSQL.

Examples:

- Jobs
- ProcessingExecutions
- Generated results
- User-facing data

---

## LangGraph State

Owned by LangGraph.

Examples:

- Current workflow step
- Intermediate outputs
- Tool responses
- LLM responses
- Temporary context

---

## TaskIQ

Does not own state.

TaskIQ only executes background tasks.

---

# Workflow State Structure

Example:

{
execution_id,
job_context,
extracted_data,
analysis_context,
tool_results,
llm_outputs,
current_node,
workflow_metadata
}

The state evolves during workflow execution.

---

# State Flow Between Nodes

Example:

Fetch Node

Input:

URL

Output:

Extracted Content

↓

Analysis Node

Input:

Extracted Content

Output:

Analysis Result

↓

LLM Node

Input:

Analysis Context

Output:

Generated Response

Each node reads and updates workflow state.

---

# Checkpointing

LangGraph checkpoints persist workflow state during execution.

Checkpointing enables:

- Workflow recovery
- Resume after interruption
- Long-running executions
- Debugging
- Execution inspection

---

# Checkpoint Ownership

Checkpoint data is not business data.

Checkpoint storage contains:

- Workflow state
- Execution position
- Node metadata

It should not replace:

- PostgreSQL records
- Domain entities
- ProcessingExecution

---

# Recovery Flow

Failure occurs

↓

Workflow checkpoint exists

↓

Execution resumes from checkpoint

↓

Workflow continues

---

# State Lifecycle

Initialized

↓

Node Execution

↓

State Update

↓

Checkpoint Saved

↓

Next Node

---

# State Versioning

Workflow state can evolve over time.

Changes to state structure should consider:

- Existing checkpoints
- Migration strategy
- Backward compatibility

Breaking state changes require a migration plan.

---

# Security

Workflow state may contain:

- User data
- External content
- LLM responses

State storage must consider:

- Access control
- Data retention
- Sensitive information handling

---

# Related Documents

- docs/ai/langgraph.md
- docs/ai/workflows.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/events.md
- docs/architecture/runtime/background-workflows.md
