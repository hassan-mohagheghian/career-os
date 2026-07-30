# Job Processing Chain

## Purpose

Defines the LangChain pipeline responsible for processing jobs.

The chain transforms job context into structured AI output.

---

## Responsibilities

The chain is responsible for:

- Building prompts
- Calling the configured executor
- Handling structured output
- Validating response schema
- Returning processing results

---

## Input

Input:

JobProcessingContext

---

## Processing Flow

JobProcessingContext

↓

Prompt Builder

↓

LangChain Chain

↓

Executor

↓

Structured Output Parser

↓

Validation

↓

Processing Result

---

## Executor

Current executor:

OpenCode

The executor is responsible for interacting with the configured LLM provider.

---

## Output

The chain produces:

- Extracted job fields
- Job summary
- Score information
- User recommendation
- Processing metadata

---

## Error Handling

Possible failures:

- Invalid LLM response
- Schema validation failure
- Timeout
- Executor failure
- Token limit exceeded

---

## Observability

The chain should record:

- Prompt version
- Schema version
- Executor name
- Execution duration
- Token usage
