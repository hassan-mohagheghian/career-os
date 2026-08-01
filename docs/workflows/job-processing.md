# Job Processing Workflow

## Purpose

This document describes the workflow responsible for processing jobs.

The workflow analyzes job information, extracts relevant data, uses AI providers, and generates scoring and career guidance.

---

# Architecture Flow

Job

↓

ProcessingExecution

↓

TaskIQ Worker

↓

LangGraph Workflow

↓

Processing Nodes

↓

Result

---

# Workflow Responsibilities

The job processing workflow is responsible for:

- Collecting job information
- Extracting structured data
- Running AI analysis
- Generating job score
- Generating career guidance
- Persisting final results

---

# Workflow Graph

START

↓

Load Job Context

↓

Fetch External Data

↓

Extract Information

↓

Normalize Data

↓

Analyze Job

↓

Generate Score

↓

Generate Career Guidance

↓

Persist Result

↓

END

---

# Node Description

## Load Job Context

Loads job information from the domain layer.

Input:

- job_id
- execution_id

Output:

- job context

---

## Fetch External Data

Retrieves additional information.

Examples:

- Company website
- External resources
- Job descriptions

Output:

- External content

---

## Extract Information

Transforms raw content into structured information.

Examples:

- Required skills
- Experience level
- Responsibilities
- Technologies

---

## Normalize Data

Creates consistent workflow input.

Examples:

- Skill normalization
- Category mapping

---

## Analyze Job

Uses AI capabilities to analyze the job.

Examples:

- Difficulty estimation
- Skill analysis
- Market relevance

---

## Generate Score

Generates job intelligence score.

Examples:

- Career fit score
- Skill match score
- Opportunity score

---

## Generate Career Guidance

Generates recommendations.

Examples:

- Required improvements
- Learning path
- Career direction

---

## Persist Result

Stores final business results.

Stored in:

PostgreSQL

---

# Workflow State

Workflow state contains:

- Job context
- Extracted information
- Analysis results
- LLM responses
- Generated insights

Workflow state is managed by LangGraph.

---

# ProcessingExecution Integration

Each workflow execution belongs to a ProcessingExecution.

ProcessingExecution tracks:

- Status
- Lifecycle
- Failure state

LangGraph tracks:

- Workflow progress
- Node execution
- Checkpoints

---

# Failure Handling

## External Data Failure

Example:

- Website unavailable

Handled by:

- Node retry
- Alternative sources

---

## LLM Failure

Example:

- Provider unavailable

Handled by:

- Retry policy
- Provider fallback

---

## Workflow Failure

Example:

- Invalid state

Handled by:

- LangGraph checkpoint recovery

---

# Progress Events

Workflow nodes emit progress events.

Example:

Fetch Data Started

↓

Extract Started

↓

Analysis Started

↓

Scoring Started

↓

Completed

Events are delivered through SSE.

Related:

docs/api/sse/processing-events.md

---

# Testing

Workflow tests should verify:

- Node behavior
- State transitions
- Failure recovery
- Provider integration
- Final result generation

---

# Related Documents

- docs/ai/workflows.md
- docs/ai/langgraph.md
- docs/ai/langgraph-state.md
- docs/domain/processing/processing-execution.md
- docs/api/processing/process-job.md
- docs/api/sse/processing-events.md
