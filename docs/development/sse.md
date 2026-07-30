# SSE Development Guide

## Purpose

Development notes for implementing Server-Sent Events.

---

## Responsibilities

FastAPI

- Maintain SSE connections
- Publish events
- Handle reconnect

Workers

- Publish execution events
- Never communicate with frontend directly

Frontend

- Open one SSE connection
- Listen for processing events
- Update local state

---

## Event Publishing

Workers publish events only when:

- status changes
- workflow step changes
- execution completes
- execution fails

---

## Best Practices

- Keep one SSE connection per browser session.
- Never open one connection per job.
- Filter events on the frontend.
- Keep event payloads small.
- Publish only state changes.
