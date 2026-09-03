# =============================================================================
# Project
# =============================================================================

variable "project_name" {
  description = "Project name used for container and volume naming"
  type        = string
  default     = "job-search"
}

# =============================================================================
# Ports
# =============================================================================

variable "postgres_port" {
  description = "Host port for PostgreSQL"
  type        = number
  default     = 5433
}

variable "redis_port" {
  description = "Host port for Redis"
  type        = number
  default     = 6380
}

variable "backend_port" {
  description = "Host port for FastAPI backend"
  type        = number
  default     = 5000
}

variable "frontend_port" {
  description = "Host port for Next.js frontend"
  type        = number
  default     = 5173
}

# =============================================================================
# PostgreSQL
# =============================================================================

variable "postgres_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "jobsearch"
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  default     = "jobsearch"
  sensitive   = true
}

variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "jobsearch"
}

# =============================================================================
# Application
# =============================================================================

variable "ai_provider" {
  description = "AI provider to use (opencode, openai, local)"
  type        = string
  default     = "opencode"
}

variable "worker_concurrency" {
  description = "Background worker concurrency"
  type        = number
  default     = 4
}
