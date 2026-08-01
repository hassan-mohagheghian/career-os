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

Update ProcessingExecution

↓

Set status COMPLETED

↓

Update Job

↓

Frontend refreshes data

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
