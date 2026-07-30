# Processing Events

## Purpose

Defines the domain events emitted during the lifecycle of a `ProcessingExecution`.

These events describe business state changes inside the Processing bounded context.

The events are independent from their delivery mechanism.

Currently they are delivered to the frontend through Server-Sent Events (SSE), but other transports (WebSocket, Redis Pub/Sub, Kafka, etc.) may be introduced in the future without changing the event definitions.

---

## Event Lifecycle

Every ProcessingExecution emits events as it progresses.

Typical lifecycle:

ExecutionQueued

↓

ExecutionStarted

↓

ExecutionStepChanged

↓

ExecutionCompleted

or

ExecutionFailed

---

## Events

### ExecutionQueued

Published when a ProcessingExecution is successfully created and added to the processing queue.

Payload:

- execution_id
- execution_type
- target_type
- target_id
- queued_at

---

### ExecutionStarted

Published when a worker begins processing the execution.

Payload:

- execution_id
- started_at

---

### ExecutionStepChanged

Published whenever the workflow enters a new processing step.

Payload:

- execution_id
- current_step
- current_step_index
- total_steps
- progress
- message
- updated_at

This event is expected to be emitted multiple times during a single execution.

---

### ExecutionCompleted

Published after the workflow successfully finishes.

Payload:

- execution_id
- completed_at
- duration

---

### ExecutionFailed

Published when processing terminates with an unrecoverable error.

Payload:

- execution_id
- failed_at
- error_code
- error_message

---

## Ordering

Events must always be emitted in chronological order.

For a single execution:

ExecutionQueued

↓

ExecutionStarted

↓

ExecutionStepChanged*

↓

ExecutionCompleted | ExecutionFailed

`ExecutionStepChanged` may occur zero or more times.

---

## Event Ownership

The Processing bounded context owns these events.

Other bounded contexts may subscribe to them, but they must never modify or publish Processing events.

---

## Delivery

The Processing bounded context only defines the events.

Transport is an infrastructure concern.

Current implementation:

- Server-Sent Events (SSE)

Possible future transports:

- WebSocket
- Redis Pub/Sub
- Kafka
- NATS
