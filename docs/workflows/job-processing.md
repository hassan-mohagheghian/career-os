# Job Processing Workflow

## Purpose

Defines the workflow responsible for processing a job using AI.

## Trigger

A ProcessingExecution with type:

JOB_PROCESSING

## Workflow Steps

1. Load ProcessingExecution

2. Load Job

3. Load Job Resources

4. Load Rules

5. Load LLM Configuration

6. Build AI Context

7. Execute AI Chain

8. Persist Result

9. Complete Execution

## Output

The workflow produces:

- Structured job information
- Summary
- Scores
- Recommendation
- Processing metadata

## Failure Handling

Any workflow failure changes execution state:

RUNNING → FAILED
