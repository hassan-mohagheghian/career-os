# Background Worker Deployment

The background worker is an independent service that can be deployed separately from the backend.

## Docker

```bash
# Build the background image
docker build -f Dockerfile.background -t job-search-background .

# Run with Redis
docker run -d --name background \
  -e REDIS_HOST=redis \
  -e REDIS_PORT=6379 \
  -v /path/to/db:/data \
  job-search-background
```

## Docker Compose

```bash
docker compose up -d background
```

## Production Considerations

- Run multiple worker instances for higher throughput
- Set `WORKER_CONCURRENCY` based on available CPU cores
- Ensure Redis is highly available (Redis Sentinel or Cluster)
- Monitor worker queues with ARQ's built-in health checks
- Configure `WORKER_JOB_TIMEOUT` appropriately for AI workflows
