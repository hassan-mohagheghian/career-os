"""RedisProcessingEventPublisher — publishes processing workflow events to
Redis pub/sub so the SSE API can stream them to frontend clients.

Publishing is best-effort: lifecycle state remains the source of truth.
"""

from __future__ import annotations

from typing import Any

from processing.application.ports.event_publisher import ProcessingEventPublisher


class RedisProcessingEventPublisher(ProcessingEventPublisher):
    def publish(
        self,
        event_name: str,
        execution_id: str,
        job_id: str | None,
        status: str,
        **kwargs: Any,
    ) -> None:
        from shared.infrastructure.events.processing_events import publish_sync

        publish_sync(event_name, execution_id, job_id, status, **kwargs)
