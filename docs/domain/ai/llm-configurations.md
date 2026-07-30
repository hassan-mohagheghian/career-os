# LLM Configuration

## Purpose

An LLM Configuration defines which Large Language Model is used by AI Tasks.

The system currently uses:

- Executor: OpenCode
- Provider: OpenAI

These values are managed by the system and are not configurable.

An LLM Configuration only controls which model should be used.

---

## Responsibilities

An LLM Configuration defines:

- Configuration Name
- Model
- Model Version
- Enabled Status

---

## Entity

| Field         | Required | Description                            |
| ------------- | -------- | -------------------------------------- |
| id            | Yes      | UUIDv7                                 |
| name          | Yes      | Configuration name                     |
| model         | Yes      | LLM model                              |
| model_version | No       | Optional model version                 |
| enabled       | Yes      | Whether this configuration can be used |
| created_at    | Yes      | Creation timestamp                     |
| updated_at    | Yes      | Last update timestamp                  |

---

## System Values

Executor

OpenCode

Provider

OpenAI

---

## Business Rules

- Name is required.
- Model is required.
- Configuration names should be unique.
- Disabled configurations cannot be selected by AI Tasks.
- Executor is fixed.
- Provider is fixed.

---

## Relationships

AI Task

↓

LLM Configuration

↓

Model
