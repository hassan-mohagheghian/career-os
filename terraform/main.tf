terraform {
  required_version = ">= 1.16.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 4.5.0"
    }
  }
}

provider "docker" {}

# =============================================================================
# Networks
# =============================================================================

resource "docker_network" "app_network" {
  name = "${var.project_name}-network"
}

# =============================================================================
# Volumes
# =============================================================================

resource "docker_volume" "pg_data" {
  name = "${var.project_name}-pg-data"
}

# =============================================================================
# Images (pull official images)
# =============================================================================

resource "docker_image" "postgres" {
  name         = "postgres:18-alpine"
  keep_locally = true
}

resource "docker_image" "redis" {
  name         = "redis:7-alpine"
  keep_locally = true
}

resource "docker_image" "node" {
  name         = "node:22-alpine"
  keep_locally = true
}

# Build custom images (Dockerfiles are in parent directory)
resource "docker_image" "backend" {
  name         = "${var.project_name}-backend:latest"
  build {
    context    = "${abspath(path.module)}/.."
    dockerfile = "Dockerfile"
  }
}

resource "docker_image" "background" {
  name         = "${var.project_name}-background:latest"
  build {
    context    = "${abspath(path.module)}/.."
    dockerfile = "Dockerfile.background"
  }
}

# =============================================================================
# PostgreSQL
# =============================================================================

resource "docker_container" "postgres" {
  name  = "${var.project_name}-postgres"
  image = docker_image.postgres.name

  ports {
    internal = 5432
    external = var.postgres_port
  }

  env = [
    "POSTGRES_USER=${var.postgres_user}",
    "POSTGRES_PASSWORD=${var.postgres_password}",
    "POSTGRES_DB=${var.postgres_db}",
  ]

  volumes {
    container_path = "/var/lib/postgresql"
    volume_name    = docker_volume.pg_data.name
  }

  networks_advanced {
    name = docker_network.app_network.name
  }

  healthcheck {
    test     = ["CMD-SHELL", "pg_isready -U ${var.postgres_user}"]
    interval = "5s"
    timeout  = "3s"
    retries  = 5
  }

  restart = "unless-stopped"
}

# =============================================================================
# Redis
# =============================================================================

resource "docker_container" "redis" {
  name  = "${var.project_name}-redis"
  image = docker_image.redis.name

  ports {
    internal = 6379
    external = var.redis_port
  }

  networks_advanced {
    name = docker_network.app_network.name
  }

  healthcheck {
    test     = ["CMD", "redis-cli", "ping"]
    interval = "5s"
    timeout  = "3s"
    retries  = 5
  }

  restart = "unless-stopped"
}

# =============================================================================
# Alembic (Migration Runner) - runs once and exits
# =============================================================================

resource "docker_container" "alembic" {
  name  = "${var.project_name}-alembic"
  image = docker_image.backend.name

  command = ["uv", "run", "alembic", "upgrade", "head"]

  env = [
    "DATABASE_URL=postgresql+psycopg://${var.postgres_user}:${var.postgres_password}@${var.project_name}-postgres:5432/${var.postgres_db}",
    "AI_PROVIDER=${var.ai_provider}",
  ]

  networks_advanced {
    name = docker_network.app_network.name
  }

  depends_on = [
    docker_container.postgres,
  ]

  # Run and exit (one-shot container)
  restart = "no"
}

# =============================================================================
# Backend (FastAPI)
# =============================================================================

resource "docker_container" "backend" {
  name  = "${var.project_name}-backend"
  image = docker_image.backend.name

  ports {
    internal = 5000
    external = var.backend_port
  }

  env = [
    "DATABASE_URL=postgresql+psycopg://${var.postgres_user}:${var.postgres_password}@${var.project_name}-postgres:5432/${var.postgres_db}",
    "REDIS_HOST=${var.project_name}-redis",
    "REDIS_PORT=6379",
    "AI_PROVIDER=${var.ai_provider}",
  ]

  networks_advanced {
    name = docker_network.app_network.name
  }

  depends_on = [
    docker_container.alembic,
    docker_container.redis,
  ]

  restart = "unless-stopped"
}

# =============================================================================
# Background Worker
# =============================================================================

resource "docker_container" "background" {
  name  = "${var.project_name}-background"
  image = docker_image.background.name

  env = [
    "DATABASE_URL=postgresql+psycopg://${var.postgres_user}:${var.postgres_password}@${var.project_name}-postgres:5432/${var.postgres_db}",
    "REDIS_HOST=${var.project_name}-redis",
    "REDIS_PORT=6379",
    "AI_PROVIDER=${var.ai_provider}",
    "WORKER_CONCURRENCY=${var.worker_concurrency}",
  ]

  networks_advanced {
    name = docker_network.app_network.name
  }

  depends_on = [
    docker_container.alembic,
    docker_container.redis,
  ]

  restart = "unless-stopped"
}

# =============================================================================
# Frontend (Next.js)
# =============================================================================

resource "docker_container" "frontend" {
  name  = "${var.project_name}-frontend"
  image = docker_image.node.name

  working_dir = "/app"
  command = [
    "sh", "-c",
    "npm install && npm run dev -- --port 5173 --host 0.0.0.0"
  ]

  ports {
    internal = 5173
    external = var.frontend_port
  }

  volumes {
    host_path      = "${abspath(path.module)}/apps/frontend"
    container_path = "/app"
  }

  env = [
    "NEXT_PUBLIC_API_URL=http://${var.project_name}-backend:5000",
  ]

  networks_advanced {
    name = docker_network.app_network.name
  }

  restart = "unless-stopped"
}
