# ARQ Processing Queue

## Purpose

Defines asynchronous processing using ARQ.

## Queue Message

The queue message contains only:

- processing_execution_id

The worker loads required data from the database.

## Worker Responsibilities

The worker:

1. Loads ProcessingExecution
2. Changes status to RUNNING
3. Executes workflow
4. Persists result
5. Updates execution status

## Worker Flow

ARQ Worker

↓

Load ProcessingExecution

↓

Execute Workflow

↓

Update Execution

## Retry Handling

The queue supports:

- Maximum retry count
- Retry delay
- Failure handling

## Failure Handling

When execution fails:

- Store error information
- Set status to FAILED
- Allow retry if applicable
