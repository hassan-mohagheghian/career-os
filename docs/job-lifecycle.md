# Job Lifecycle

## Overview

The Job lifecycle describes the complete journey from when a user submits a new job URL until it reaches its final state in the UI. Every Job follows one deterministic lifecycle with exactly one authoritative status at any time.

## Flow

```
User submits URL (CLI or Web UI)
         ↓
    POST /api/pending          (creates record, status=created)
         ↓
    POST /api/pending/{id}/process  OR auto_enqueue
         ↓
    JobQueueManager.enqueue(id)  (status→queued)
         ↓
    Worker picks up item         (status→starting)
         ↓
    LangGraph Workflow:
      load_context      → starting
      validate_input    → starting
      fetch_url         → fetching
      fallback_to_notes → fetching
      extract_raw       → analyzing
      clean_content     → analyzing
      extract_structured → analyzing
      analyze_job       → analyzing
      extract_skills    → analyzing
      score_job         → generating
      generate_summary  → generating
      persist_results   → finalizing
      completion_event  → finalizing
         ↓
    completed  OR  failed  OR  cancelled
```

## Key Principles

### Single Source of Truth
Status comes exclusively from the backend database (`pending_jobs.status` column). It is never inferred from:
- Temporary files
- Queue position
- Frontend state

### FastAPI Only Orchestrates
FastAPI endpoints only:
1. Validate input
2. Create the Job record
3. Enqueue via ARQ/JobQueueManager
4. Return immediately

All processing happens in background workers.

### LangGraph Owns Workflow State
The LangGraph workflow manages execution state in memory. Each node updates the job status and emits progress events. No intermediate files are written to disk.

## Job Statuses

| Status      | Meaning                                          | Terminal |
|-------------|--------------------------------------------------|----------|
| created     | Job record created, not yet queued               | No       |
| queued      | Enqueued in the background worker queue           | No       |
| waiting     | Awaiting manual start or resource availability    | No       |
| starting    | Initializing workflow context and validation      | No       |
| fetching    | Fetching URL content and notes                    | No       |
| analyzing   | Extracting and analyzing job data                 | No       |
| generating  | Scoring and generating summary                    | No       |
| finalizing  | Persisting results to database                    | No       |
| completed   | Processing finished successfully                  | Yes      |
| failed      | Processing encountered an unrecoverable error     | Yes      |
| cancelled   | Processing was cancelled by user                  | Yes      |

## Transitions

```
created ──→ queued ──→ waiting ──→ starting ──→ fetching ──→ analyzing
  ↑           ↑           ↑            │              │            │
  │           │           │            │              │            │
  │           │           └────────────┼──────────────┼────────────┼──→ failed
  │           │           ┌────────────┼──────────────┼────────────┼──→ cancelled
  │           │           │            │              │            │
  │           └───────────┼────────────┼──────────────┼────────────┤
  └───────────────────────┼────────────┼──────────────┼────────────┤
                          │            │              │            │
                          ↓            ↓              ↓            ↓
                     generating ──→ finalizing ──→ completed
                          │              │
                          ├──→ failed     ├──→ failed
                          └──→ cancelled   └──→ cancelled

completed ──→ queued    (reprocess)
completed ──→ cancelled
failed ──→ queued        (retry)
failed ──→ cancelled
cancelled ──→ created    (un-cancel)
cancelled ──→ queued     (un-cancel and requeue)
```

## Error Handling

When a job fails:
- `status` is set to `failed`
- `error` contains the error message
- `failure_details` contains structured failure info:
  - `workflow_step` - which LangGraph node failed
  - `provider` - AI provider used
  - `exception` - exception message
  - `retry_count` - number of retry attempts
  - `recoverable` - whether the job can be retried

## Recovery

On server restart:
1. Jobs in `starting`, `fetching`, `analyzing`, `generating`, or `finalizing` are moved to `created`
2. Their `previous_status` is preserved
3. Users can manually re-queue them
