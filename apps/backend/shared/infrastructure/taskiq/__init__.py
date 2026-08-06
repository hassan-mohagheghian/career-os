"""TaskIQ infrastructure for the shared layer.

The TaskIQ queue implementation is an infrastructure concern. Business logic
must not depend directly on TaskIQ — it interacts through application services
and the taskiq client helpers.
"""

from shared.infrastructure.taskiq.config import broker, build_broker
from shared.infrastructure.taskiq.client import (
    enqueue_execution,
    enqueue_execution_sync,
    enqueue_generation,
    enqueue_generation_sync,
)
from shared.infrastructure.taskiq.tasks import (
    process_execution_task,
    process_generation_task,
)

__all__ = [
    "broker",
    "build_broker",
    "enqueue_generation",
    "enqueue_generation_sync",
    "enqueue_execution",
    "enqueue_execution_sync",
    "process_generation_task",
    "process_execution_task",
]
