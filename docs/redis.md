# Redis

## Purpose

Redis is an infrastructure component used by the platform for fast data access and asynchronous communication.

Redis is not a source of business truth.

Business data belongs to PostgreSQL.

Redis is used only for temporary or infrastructure-level concerns.

---

# Current Usage

Redis is used for:

- TaskIQ message broker
- Temporary task communication
- Caching
- Distributed coordination when required

---

# TaskIQ Integration

Redis acts as the message broker for TaskIQ.

Architecture:

API

↓

ProcessingExecution

↓

TaskIQ Task

↓

Redis Broker

↓

TaskIQ Worker

↓

LangGraph Workflow

Redis responsibilities:

- Store pending tasks
- Deliver tasks to workers
- Manage task communication

Redis does not manage:

- Workflow state
- Job lifecycle
- Processing results
- Business entities

---

# Workflow State

Workflow state is not stored in Redis.

LangGraph workflow state is persisted through checkpointing mechanisms.

Business execution state is stored in:

- PostgreSQL
- ProcessingExecution records

---

# Data Ownership

## PostgreSQL

Source of truth for:

- Jobs
- Processing executions
- Results
- Domain entities

## Redis

Temporary infrastructure storage for:

- Queue messages
- Cache entries
- Short-lived coordination data

---

# Previous ARQ Usage

The previous architecture used Redis as the ARQ queue backend.

Previous:

API

↓

ARQ

↓

Redis Queue

↓

ARQ Worker

This architecture is deprecated.

Current:

API

↓

TaskIQ

↓

Redis Broker

↓

TaskIQ Worker

---

# Deployment

Redis runs as an independent infrastructure service.

Production components:

- FastAPI
- TaskIQ Workers
- Redis
- PostgreSQL

Redis availability affects:

- Background task execution
- Queue communication

Redis failure does not corrupt business data.

---

# Monitoring

Redis monitoring should include:

- Memory usage
- Connection count
- Queue size
- Command latency
- Eviction rate
- Availability

For TaskIQ monitoring also check:

- Pending tasks
- Failed tasks
- Worker connectivity

---

# Related Documents

- docs/architecture/runtime/background-service.md
- docs/queue/processing/taskiq-processing.md
- docs/adr/019-taskiq-migration.md
- docs/domain/processing/processing-execution.md
