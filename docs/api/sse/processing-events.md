# Processing Events API

## Endpoint

GET /events/processing

---

## Purpose

Streams live ProcessingExecution events.

---

## Event Types

ExecutionQueued

ExecutionStarted

ExecutionStepChanged

ExecutionCompleted

ExecutionFailed

---

## Event Payload

Each event contains:

- execution_id
- job_id
- status
- current_step
- progress
- message
- updated_at

---

## Authentication

Uses the same authentication mechanism as the REST API.

---

## Reconnection

Clients should automatically reconnect using the Last-Event-ID header.
