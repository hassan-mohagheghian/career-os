# Background Workflows

All long-running AI workflows execute inside the Background worker application.

## Job Processing

1. Backend validates input and schedules via ARQ
2. ARQ worker picks up the job
3. Worker creates `JobWorker` with the LangGraph job graph
4. LangGraph executes the 12-stage pipeline
5. Results are persisted to the shared database

## Company Processing

1. Backend creates pending company record and schedules via ARQ
2. ARQ worker picks up the company
3. Worker creates `CompanyWorker` with the LangGraph company graph
4. LangGraph executes: fetch → extract → analyze → score → save
5. Results are persisted to the shared database

## Resume / Cover Letter Generation

1. Backend creates generation record and schedules via ARQ
2. ARQ worker picks up the generation request
3. Worker calls `process_generation()` with the LLM service
4. Generated document is saved to the database
5. Status is broadcast via WebSocket

## Retry Strategy

- ARQ handles retries automatically (configurable via `WORKER_MAX_RETRIES`)
- Failed jobs are marked in the database with error details
- Manual retry is available via the API
