"""Assembly — wires real infrastructure into the job and company processing graphs.

This is the single place where infrastructure adapters are chosen for the
job/company context preparation and analysis workflows. Future providers
(Firecrawl, Jina Reader, ...) can be added here without touching application
or domain layers.
"""

from __future__ import annotations

from typing import Any

from ai.infrastructure.service import get_llm_service
from companies.application.services.company_matching_service import CompanyMatchingService
from companies.application.services.company_service import CompanyService
from companies.infrastructure.repositories.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
from companies.infrastructure.repositories.sa_company_repository import SQLAlchemyCompanyRepository
from jobs.application.services.job_service import JobService
from jobs.infrastructure.repositories.sa_job_analysis_repository import SQLAlchemyJobAnalysisRepository
from jobs.infrastructure.repositories.sa_job_company_repository import SQLAlchemyJobCompanyRepository
from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
from jobs.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
from processing.application.workflows.company_analysis import CompanyAnalysisGraph
from processing.application.workflows.company_context_preparation import CompanyContextPreparationGraph
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
        matching_service=CompanyMatchingService(SQLAlchemyCompanyRepository(session)),
        job_company_repo=SQLAlchemyJobCompanyRepository(session),
        llm_service=get_llm_service(),
        event_publisher=event_publisher,
    )


def _company_service(session: Any) -> CompanyService:
    return CompanyService(
        repository=SQLAlchemyCompanyRepository(session),
        intelligence_repository=SQLAlchemyCompanyIntelligenceRepository(session),
    )


def build_company_context_preparation_graph(session: Any) -> CompanyContextPreparationGraph:
    """Build the Company context preparation graph (no LLM)."""
    fetcher = CompositeContentFetcher(
        [HTTPXContentFetcher(), PlaywrightContentFetcher()]
    )
    extractor = CompositeContentExtractor(
        [TrafilaturaContentExtractor(), BeautifulSoupContentExtractor()]
    )
    event_publisher = RedisProcessingEventPublisher()

    return CompanyContextPreparationGraph(
        company_service=_company_service(session),
        fetcher=fetcher,
        extractor=extractor,
        event_publisher=event_publisher,
    )


def build_company_analysis_graph(session: Any) -> CompanyAnalysisGraph:
    """Build the Company analysis graph with production infrastructure adapters."""
    return CompanyAnalysisGraph(
        company_service=_company_service(session),
        rule_repo=SQLAlchemyRuleRepository(session),
        llm_service=get_llm_service(),
        event_publisher=RedisProcessingEventPublisher(),
    )
