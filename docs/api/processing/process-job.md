# Process Job API

## Purpose

Creates a processing execution for a job.

## Endpoint

POST /jobs/{jobId}/process

## Responsibilities

The API performs:

1. Validate job
2. Create ProcessingExecution
3. Add execution to ARC queue
4. Return execution information

## Request

Path parameter:

- jobId

## Response

HTTP Status:

202 Accepted

Response fields:

- execution_id
- status

Example:

status: QUEUED

## Validation

The API validates:

- Job exists
- Job is processable
- No active execution exists

## Error Cases

### 404 Not Found

Job does not exist.

### 409 Conflict

An active execution already exists.

### 422 Validation Error

Processing request is invalid.
