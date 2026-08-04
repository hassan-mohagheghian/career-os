# Prompt: Connect the New Jobs UI to the New Backend APIs

This prompt is a continuation of the previous implementation.

Assume the new Feature-Sliced Jobs UI has already been implemented.

Your task is to replace all mocked data with the new backend APIs while keeping the legacy implementation untouched.

---

# Read These Documents

## Frontend

* docs/feature-sliced-design.md
* docs/frontend-architecture.md
* docs/frontend-sync.md

## UX

* docs/ux/features/jobs/page.md

* docs/ux/features/jobs/job-row.md

* docs/ux/features/jobs/processing-queue.md

* docs/ux/flows/jobs/browse-jobs.md

* docs/ux/flows/jobs/process-job.md

* docs/ux/flows/jobs/process-job-live.md

---

## API

* docs/api/jobs/list-jobs.md
* docs/api/processing/process-job.md
* docs/api/sse/processing-events.md

---

## Domain

* docs/domain/jobs/job-list-item.md
* docs/domain/jobs/job-search.md
* docs/domain/processing/processing-execution.md
* docs/domain/processing/events.md

---

## Queue

* docs/queue/processing/arq-processing.md

---

## AI

* docs/ai/job-processing-context.md
* docs/ai/job-processing-chain.md

---

# Goal

The new Jobs page must communicate with the new backend.

No mocked data should remain.

---

# Requirements

## 1. Load Jobs

Replace mocked jobs with

GET /api/jobs

using TanStack Query.

Implement

* loading state
* error state
* empty state
* refetch
* pagination
* filters
* sorting
* searching

following

docs/api/jobs/list-jobs.md

---

## 2. Processing Button

The new

Process V2

button should call

POST /api/processing/jobs/{jobId}

The legacy Process button must remain unchanged.

---

## 3. Optimistic UI

Immediately after Process V2 is clicked

update the row

for example

Idle

↓

Queued

without waiting for the server response.

Rollback if the request fails.

---

## 4. Queue Drawer

Replace mocked queue items.

Load them from the backend.

Use the ProcessingExecution model.

Display

* queued
* starting
* running
* completed
* failed
* cancelled

---

## 5. Live Updates

Implement Server-Sent Events.

Subscribe when the Jobs page opens.

Endpoint

GET /api/processing/events

Use the event definitions from

docs/api/sse/processing-events.md

Reconnect automatically.

Do not use polling.

Do not use WebSockets.

---

## 6. Update Job Rows

Whenever an SSE event is received

update only the affected row.

Never reload the entire page.

Use TanStack Query cache updates.

Examples

queryClient.setQueryData()

invalidateQueries()

only when necessary.

---

## 7. Queue Synchronization

The Queue Drawer and Jobs List must always stay synchronized.

If a ProcessingExecution changes

both views must update immediately.

---

## 8. Processing Status

Render every ProcessingExecution state.

Unknown states must never crash the UI.

Fallback

Unknown

---

## 9. Placeholder Fields

If the backend still doesn't provide

Location

Remote

Visa

Scores

Logo

etc.

continue displaying the existing placeholders.

Do not block rendering.

---

## 10. Error Handling

Display user-friendly errors.

Examples

Cannot start processing

Connection lost

SSE disconnected

Retry available

---

## 11. Performance

Avoid unnecessary renders.

Avoid full page refreshes.

Avoid refetching all jobs after every event.

Update only the changed entities.

---

## 12. TanStack Query

Use

Queries

Mutations

Optimistic updates

Cache synchronization

Invalidate only when required.

---

## 13. Feature-Sliced Rules

Do not place API calls inside UI components.

Create proper

api/

model/

lib/

hooks/

inside each feature/entity.

---

## 14. Legacy Compatibility

Do NOT modify

the deprecated Jobs page.

Do NOT remove

legacy endpoints.

Do NOT replace

legacy Process workflow.

Everything new must coexist beside the old implementation.

---

# Deliverables

Implement

* Real Jobs API integration
* Real Processing API integration
* SSE client
* Live row updates
* Queue synchronization
* Optimistic mutations
* TanStack Query cache management
* Feature-Sliced API layer

Do NOT implement

* LangGraph execution
* Worker logic
* ARQ internals
* Processing pipeline
* AI workflow

Assume the backend already exposes the documented endpoints and event contracts.
