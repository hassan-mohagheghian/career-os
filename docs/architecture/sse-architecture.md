# SSE Architecture

## Purpose

Describe how the backend streams processing events to the frontend.

The system uses Server-Sent Events (SSE) to provide live updates while background executions are running.

---

## Why SSE

The processing pipeline only requires server-to-client communication.

Workers never receive commands directly from the frontend.

SSE provides:

- HTTP based
- One-way communication
- Automatic reconnect
- Simple implementation
- Low overhead

---

## Architecture

Frontend

↓

SSE Connection

↓

FastAPI

↓

Event Broadcaster

↓

ARQ Worker

↓

Workflow

---

## Event Source

Only ProcessingExecution may publish events.

Workers never communicate directly with the frontend.

All updates pass through the Event Broadcaster.

---

## Connection Lifecycle

Client opens connection

↓

Receive events

↓

Automatic reconnect if disconnected

↓

Connection closes when page is closed
