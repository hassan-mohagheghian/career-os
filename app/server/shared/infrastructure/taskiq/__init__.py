"""TaskIQ infrastructure for the shared layer.

The TaskIQ queue implementation is an infrastructure concern. Business logic
must not depend directly on TaskIQ — it interacts through application services
and the taskiq client helpers.
"""

from shared.infrastructure.taskiq.config import broker, build_broker
from shared.infrastructure.taskiq.client import (
    enqueue_company,
    enqueue_company_sync,
    enqueue_execution,
    enqueue_execution_sync,
    enqueue_generation,
    enqueue_generation_sync,
    enqueue_job,
    enqueue_job_sync,
)
from shared.infrastructure.taskiq.tasks import (
    process_company_task,
    process_execution_task,
    process_generation_task,
    process_job_task,
)

__all__ = [
    "broker",
    "build_broker",
    "enqueue_job",
    "enqueue_job_sync",
    "enqueue_company",
    "enqueue_company_sync",
    "enqueue_generation",
    "enqueue_generation_sync",
    "enqueue_execution",
    "enqueue_execution_sync",
    "process_job_task",
    "process_company_task",
    "process_generation_task",
    "process_execution_task",
]
