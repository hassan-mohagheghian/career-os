# Processing Execution

## Purpose

The Processing bounded context manages the lifecycle of background executions across the platform.

A `ProcessingExecution` represents one execution attempt of an asynchronous operation.

Examples:

- Job processing
- Cover letter generation
- Resume tailoring
- Company analysis
- Insight generation

## Responsibilities

ProcessingExecution is responsible for:

- Tracking execution lifecycle
- Managing execution status
- Linking execution to the target resource
- Tracking execution metadata
- Supporting retries and failures
- Providing execution history

## Entity Definition

ProcessingExecution

Fields:

- id: UUIDv7
- type: ExecutionType
- status: ExecutionStatus
- target_id
- target_type
- created_at
- started_at
- finished_at
- retry_count
- error_message

## Execution Types

Examples:

- JOB_PROCESSING
- COVER_LETTER_GENERATION
- RESUME_TAILORING
- COMPANY_ANALYSIS
- INSIGHT_GENERATION

## Status

Supported statuses:

- PENDING
- QUEUED
- RUNNING
- COMPLETED
- FAILED
- CANCELLED

## Lifecycle

PENDING

↓

QUEUED

↓

RUNNING

↓

COMPLETED

Failure:

RUNNING

↓

FAILED

## Business Rules

- Every execution must have a target resource.
- Every execution must have a defined execution type.
- Completed executions are immutable.
- Failed executions may be retried.
- Every execution must be traceable.
