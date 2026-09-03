# Terraform Local Deployment

This directory contains Terraform configuration for deploying the Job Search platform locally using Docker.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.16.0
- [Docker](https://docs.docker.com/get-docker/) running locally
- Docker provider plugin (installed automatically)

## Quick Start

```bash
cd terraform

# Initialize Terraform
terraform init

# Review the execution plan
terraform plan

# Apply the configuration
terraform apply

# When prompted, type 'yes' to confirm
```

## Configuration

### Using Variables

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your preferred values:
   ```hcl
   project_name = "my-project"
   backend_port = 8000
   postgres_password = "secure-password"
   ```

3. Apply with your custom configuration:
   ```bash
   terraform apply -var-file="terraform.tfvars"
   ```

### Available Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Project name for containers/volumes | `job-search` |
| `postgres_port` | Host port for PostgreSQL | `5432` |
| `redis_port` | Host port for Redis | `6379` |
| `backend_port` | Host port for FastAPI backend | `5000` |
| `frontend_port` | Host port for Next.js frontend | `5173` |
| `postgres_user` | PostgreSQL username | `jobsearch` |
| `postgres_password` | PostgreSQL password | `jobsearch` |
| `postgres_db` | PostgreSQL database name | `jobsearch` |
| `ai_provider` | AI provider (opencode, openai, local) | `opencode` |
| `worker_concurrency` | Background worker concurrency | `4` |

## Services

After applying, the following services will be running:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | Next.js UI |
| Backend API | http://localhost:5000 | FastAPI backend |
| Swagger UI | http://localhost:5000/api/docs | API documentation |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Message broker |

## Commands

```bash
# View current state
terraform state list

# Destroy all resources
terraform destroy

# Plan before applying
terraform plan

# Apply with auto-approve (no prompt)
terraform apply -auto-approve

# Refresh state
terraform refresh

# Show outputs
terraform output
```

## Data Persistence

- PostgreSQL data is stored in a Docker volume: `job-search-pg-data`
- To remove all data: `terraform destroy` and delete the volume

## Troubleshooting

### Port Conflicts

If ports are already in use, update `terraform.tfvars`:
```hcl
postgres_port = 54320
redis_port    = 6380
backend_port  = 8000
frontend_port = 3000
```

### Container Logs

```bash
# View logs for a specific service
docker logs job-search-backend
docker logs job-search-frontend
docker logs job-search-postgres
```

### Reset Everything

```bash
terraform destroy -auto-approve
docker volume rm job-search-pg-data
```

## Differences from Docker Compose

| Feature | Docker Compose | Terraform |
|---------|----------------|-----------|
| State management | Implicit | Explicit (terraform.tfstate) |
| Dependency tracking | `depends_on` | `depends_on` + implicit |
| Idempotency | Partial | Full |
| Plan before apply | No | Yes |
| Output values | Limited | Rich outputs |
| Variable validation | Basic | Advanced with types |

## Notes

- Terraform manages Docker resources similarly to Docker Compose
- State is stored in `terraform.tfstate` (add to `.gitignore`)
- The `alembic` container runs once and exits (migration runner)
- All other containers use `restart = "unless-stopped"`

## Versions Used

| Component | Version |
|-----------|---------|
| Terraform | >= 1.16.0 |
| Docker Provider | ~> 4.5.0 (kreuzwerker/docker) |
| PostgreSQL | 18-alpine |
| Redis | 7-alpine |
| Node.js | 22-alpine |
