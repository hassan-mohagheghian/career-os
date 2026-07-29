# Redis

Redis is used as the message broker for ARQ job queues.

## Responsibilities

- **Queue**: ARQ job queue storage
- **Scheduling**: Cron-based periodic job scheduling
- **Worker Coordination**: Worker heartbeat and coordination

Redis does NOT store business data. All business persistence is via SQLite/SQLAlchemy.

## Requirements

- Redis 7+ (Alpine image recommended for Docker)
- No persistence configuration needed (queue data is transient)

## Local Development

```bash
# Start Redis via Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Or via docker compose
docker compose up redis -d
```
