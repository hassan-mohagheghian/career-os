"""Assembly — wires real infrastructure into the job processing graphs.

This is the single place where infrastructure adapters are chosen for the
job context preparation and job analysis workflows. Future providers
(Firecrawl, Jina Reader, ...) can be added here without touching application
or domain layers.
"""

from __future__ import annotations

from typing import Any

from ai.infrastructure.service import get_llm_service
from jobs.application.services.job_service import JobService
from jobs.infrastructure.repositories.sa_job_analysis_repository import SQLAlchemyJobAnalysisRepository
from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
from jobs.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
from processing.application.workflows.job_analysis import JobAnalysisGraph
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
from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository
from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository


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


def build_job_analysis_graph(session: Any) -> JobAnalysisGraph:
    """Build the Job Analysis graph with production infrastructure adapters."""
    job_repo = SQLAlchemyJobRepository(session)
    job_service = JobService(job_repo)
    event_publisher = RedisProcessingEventPublisher()

    return JobAnalysisGraph(
        job_service=job_service,
        skill_repo=SQLAlchemySkillRepository(session),
        resume_repo=SQLAlchemyResumeRepository(session),
        rule_repo=SQLAlchemyRuleRepository(session),
        job_repo=job_repo,
        summary_repo=SQLAlchemySummaryRepository(session),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        llm_service=get_llm_service(),
        event_publisher=event_publisher,
    )
