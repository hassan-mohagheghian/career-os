# Process Job Flow

## Purpose

Defines the complete flow from user action to completed job processing.

---

## Trigger

User clicks:

Process Job

---

## Flow

User

↓

Frontend Process Button

↓

POST /jobs/{jobId}/process

↓

Create ProcessingExecution

↓

Set status QUEUED

↓

Push execution to TaskIQ queue

↓

Worker receives execution

↓

Load Job

↓

Load Resources

↓

Load Rules

↓

Load LLM Configuration

↓

Build Job Processing Context

↓

Execute LangChain Chain

↓

OpenCode Executor

↓

Receive Structured Output

↓

Persist Processing Result

↓

Persist Skills

↓

Link Companies

↓

Update ProcessingExecution

↓

Set status COMPLETED

↓

Update Job

↓

Frontend refreshes data

---

## Company Linking

During processing the AI extracts a `hiring_company` (the employer, only when
there is solid evidence — it is never guessed) plus zero or more
`related_companies` (recruiting / staffing / consulting agencies). After the
analysis is persisted, the workflow resolves each company via find-or-create
and stores the associations in the `job_companies` table:

- The **hiring company** drives the job's `company_id` / display name.
- **Related companies** are stored with `role="recruiter"` and shown in the Job
  Detail drawer under **Published by**; recruiter companies show their
  hiring-client jobs under **Jobs listed for clients** in the Company Detail
  drawer.
- Associations are **replaced** on every re-process, so a re-run with changed
  extraction never leaves stale recruiter rows.

Company resolution is best-effort: a failure to resolve a company never fails
the job execution.

---

## Failure Flow

Processing Failure

↓

Update Execution Status

↓

FAILED

↓

Store Error Information

↓

Allow Retry
