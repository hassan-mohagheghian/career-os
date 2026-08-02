"""Assembly — wires real infrastructure into the JobContextPreparationGraph.

This is the single place where infrastructure adapters are chosen for the
job context preparation workflow. Future providers (Firecrawl, Jina Reader,
...) can be added here without touching application or domain layers.
"""

from __future__ import annotations

from typing import Any

from jobs.application.services.job_service import JobService
from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
from processing.application.workflows.job_context_preparation import JobContextPreparationGraph
from processing.infrastructure.content import (
    BeautifulSoupContentExtractor,
    CompositeContentExtractor,
    CompositeContentFetcher,
    HTTPXContentFetcher,
    PlaywrightContentFetcher,
    TrafilaturaContentExtractor,
)
from processing.infrastructure.events import RedisProcessingEventPublisher


def build_job_context_preparation_graph(session: Any) -> JobContextPreparationGraph:
    """Build the graph with production infrastructure adapters."""
    job_repo = SQLAlchemyJobRepository(session)
    job_service = JobService(job_repo)

    fetcher = CompositeContentFetcher(
        [HTTPXContentFetcher(), PlaywrightContentFetcher()]
    )
    extractor = CompositeContentExtractor(
        [TrafilaturaContentExtractor(), BeautifulSoupContentExtractor()]
    )
    event_publisher = RedisProcessingEventPublisher()

    return JobContextPreparationGraph(
        job_service=job_service,
        fetcher=fetcher,
        extractor=extractor,
        event_publisher=event_publisher,
    )
