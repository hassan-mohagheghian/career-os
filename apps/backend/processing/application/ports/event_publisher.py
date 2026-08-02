"""ProcessingEventPublisher — application interface for emitting workflow
events (processing.started, processing.loading_job, ...).

Events are consumed later by the SSE API and frontend workflow visualization.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProcessingEventPublisher(ABC):
    @abstractmethod
    def publish(
        self,
        event_name: str,
        execution_id: str,
        job_id: str | None,
        status: str,
        **kwargs: Any,
    ) -> None:
        """Publish a processing event. Implementations must be best-effort."""
        ...
