# Prompt 056 - Migrate Background Processing From ARQ To TaskIQ

## Objective

Migrate the existing background processing system from ARQ to TaskIQ.

The goal is to replace ARQ completely while keeping the current business behavior unchanged.

The new architecture must follow:

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

Processing Result

---

## Read These Documents First

Before making any changes, read:

- docs/adr/019-taskiq-migration.md
- docs/architecture/runtime/background-service.md
- docs/architecture/runtime/background-workflows.md
- docs/architecture/runtime/workflow-progress.md
- docs/queue/processing/taskiq-processing.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/events.md
- docs/api/processing/process-job.md
- docs/api/sse/processing-events.md
- docs/ai/workflows.md
- docs/ai/langgraph.md
- docs/ai/langgraph-state.md

---

## Current State

The project currently uses ARQ for background execution.

Existing ARQ-related components may include:

- ARQ worker configuration
- ARQ task definitions
- Redis queue configuration
- Worker startup commands
- Deployment configuration
- Background processing services

---

## Migration Requirements

Replace ARQ with TaskIQ.

The migration must include:

### 1. TaskIQ Infrastructure

Implement:

- TaskIQ broker configuration
- Redis broker setup
- Worker configuration
- Task discovery
- Worker startup

Do not create a custom queue system.

Use TaskIQ native patterns.

---

### 2. Replace ARQ Tasks

For every ARQ task:

Find the equivalent TaskIQ task.

Preserve:

- Input parameters
- Business behavior
- Error handling
- Retry behavior

Move business logic out of tasks if needed.

Tasks should only coordinate execution.

---

### 3. Worker Migration

Replace ARQ worker processes with TaskIQ workers.

Update:

- Worker entrypoints
- Development commands
- Production commands
- Deployment configuration

Remove:

- ARQ worker startup
- ARQ dependencies
- ARQ-specific configuration

---

### 4. Redis Usage

Keep Redis.

Redis remains responsible for:

- TaskIQ message broker
- Background task communication

Redis must not become:

- Workflow state storage
- Business data storage

---

### 5. ProcessingExecution Integration

TaskIQ execution must integrate with ProcessingExecution.

Required flow:

Create ProcessingExecution

↓

Dispatch TaskIQ task

↓

Update execution status

↓

Run workflow

↓

Complete or fail execution

Do not expose TaskIQ concepts to the domain layer.

---

### 6. LangGraph Integration

TaskIQ should start LangGraph workflow execution.

The responsibility boundary:

TaskIQ:

- Execute background task
- Handle retries
- Start worker execution

LangGraph:

- Execute workflow graph
- Manage workflow state
- Handle checkpoints
- Manage node execution

---

### 7. Error Handling

Preserve failure handling.

Infrastructure failures:

Examples:

- Worker crash
- Redis unavailable

Handled by:

- TaskIQ retries

Workflow failures:

Examples:

- LLM failure
- Node failure

Handled by:

- LangGraph checkpointing
- Workflow recovery

---

## Documentation Updates

Update documentation after implementation.

Update:

- docs/queue/processing/taskiq-processing.md
- docs/architecture/runtime/background-service.md
- docs/architecture/runtime/background-workflows.md
- docs/deployment/background.md
- docs/development/developer-workflow.md

Add migration notes where necessary.

---

## Remove ARQ

After successful migration:

Remove:

- ARQ dependencies
- ARQ configuration
- ARQ worker code
- ARQ task definitions
- ARQ deployment references

Do not remove historical documentation:

Keep:

- docs/arq.md
- docs/queue/processing/arq-processing.md

Mark them as deprecated.

---

## Testing Requirements

Verify:

- Task creation works
- Worker starts successfully
- Tasks execute correctly
- Retries work
- ProcessingExecution lifecycle works
- Workflow execution starts
- SSE progress events are emitted

---

## Implementation Rules

Follow existing architecture rules:

- Keep domain independent from infrastructure
- Follow modular monolith boundaries
- Keep background execution separate from workflow execution
- Avoid introducing unnecessary abstractions
- Prefer existing application services

---

## Expected Result

After migration:

API

↓

ProcessingExecution

↓

TaskIQ

↓

Redis Broker

↓

TaskIQ Worker

↓

LangGraph Workflow

↓

Results + Events

ARQ should no longer be part of runtime execution.
