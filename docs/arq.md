# ARQ (Async Job Queue)

ARQ is the background processing framework for the Job Search platform.

## Overview

ARQ is a Python async job queue backed by Redis. It replaces the previous thread-based queue manager and provides:

- Async worker processes
- Built-in retry logic
- Job timeout handling
- Cron scheduling
- Redis-backed persistence

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | `` | Redis password |
| `ARQ_QUEUE_NAME` | `arq:queue` | Queue key prefix |
| `WORKER_CONCURRENCY` | `4` | Concurrent worker count |
| `WORKER_MAX_RETRIES` | `3` | Max retry attempts |
| `WORKER_JOB_TIMEOUT` | `600` | Job timeout in seconds |

## Enqueuing Jobs

```python
from shared.infrastructure.queue.arq_client import enqueue_job_sync

# From sync code
enqueue_job_sync(job_id)

# From async code
await enqueue_process_job(job_id)
```
