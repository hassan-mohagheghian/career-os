# Background Service Architecture

## Purpose

This document describes the background execution architecture of the platform.

The background service is responsible for executing long-running operations without blocking API requests.

Examples:

- Job processing
- URL fetching
- Content extraction
- LLM analysis
- Scoring generation
- Workflow execution

The background system separates:

- Request handling
- Execution lifecycle
- Task execution
- Workflow orchestration

---

# Architecture Overview

The background processing architecture consists of four layers:

1. API Layer
2. Domain Execution Layer
3. Task Execution Layer
4. Workflow Layer

## API Layer

The API layer receives user requests.

Responsibilities:

- Validate request
- Create ProcessingExecution
- Return execution identifier
- Provide status endpoints

The API does not execute long-running operations directly.

Flow:

API Request

↓

Create ProcessingExecution

↓

Dispatch Background Task

↓

Return Response

---

# Domain Execution Layer

Main component:

ProcessingExecution

Location:

docs/domain/processing/processing-execution.md

Responsibilities:

- Represent a processing attempt
- Track execution status
- Store execution metadata
- Manage execution lifecycle

ProcessingExecution is independent from background infrastructure.

The domain layer must not know:

- TaskIQ
- Redis
- Worker implementation

---

# Task Execution Layer

Main component:

TaskIQ

TaskIQ is responsible for:

- Running background tasks
- Managing workers
- Handling retries
- Scheduling execution
- Communicating with Redis

TaskIQ receives execution requests and starts the workflow.

Architecture:

ProcessingExecution

↓

TaskIQ Task

↓

TaskIQ Worker

---

# Workflow Layer

Main component:

LangGraph

LangGraph is responsible for:

- Workflow definition
- State management
- Node execution
- Checkpointing
- Recovery
- Progress generation

Example workflow:

Fetch URL

↓

Extract Content

↓

Analyze Content

↓

Call LLM Provider

↓

Generate Score

↓

Persist Result

---

# Redis Usage

Redis is used as the TaskIQ broker.

Redis responsibilities:

- Queue pending tasks
- Deliver tasks to workers
- Manage task communication

Redis is not the source of business state.

Business state is stored in:

- PostgreSQL
- ProcessingExecution records
- LangGraph checkpoints

---

# Worker Architecture

Background workers run independently from API services.

Worker responsibilities:

- Connect to TaskIQ broker
- Receive tasks
- Execute workflows
- Report execution results

Worker lifecycle:

Start Worker

↓

Connect Redis

↓

Wait For Task

↓

Execute Workflow

↓

Update Execution

↓

Complete

---

# Error Handling

Failures are separated into two categories.

## Infrastructure Failures

Examples:

- Redis unavailable
- Worker crash
- Temporary network failure

Handled by:

- TaskIQ retry mechanism

---

## Workflow Failures

Examples:

- LLM failure
- Extraction failure
- Invalid workflow state

Handled by:

- LangGraph checkpointing
- ProcessingExecution state management

---

# Scaling Model

The background system can scale independently.

API scaling:

Add more API instances.

Worker scaling:

Add more TaskIQ workers.

Workflow scaling:

Optimize LangGraph execution.

Example:

API Instances

-

TaskIQ Workers

-

Redis

-

PostgreSQL

---

# Deployment

Production components:

- FastAPI service
- TaskIQ worker service
- Redis broker
- PostgreSQL database

Deployment relationship:

FastAPI

↓

TaskIQ + Redis

↓

Workers

↓

LangGraph

↓

Database

---

# Migration From Previous Architecture

Previous:

API

↓

ARQ

↓

ARQ Worker

↓

Processing

Current:

API

↓

ProcessingExecution

↓

TaskIQ

↓

TaskIQ Worker

↓

LangGraph Workflow

---

# Related Documents

- docs/adr/019-taskiq-migration.md
- docs/queue/processing/taskiq-processing.md
- docs/domain/processing/processing-execution.md
- docs/workflows/job-processing.md
- docs/ai/workflows.md
- docs/api/processing/process-job.md
- docs/architecture/runtime/redis.md
