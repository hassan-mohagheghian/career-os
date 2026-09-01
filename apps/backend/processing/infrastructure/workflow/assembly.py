"""Assembly — wires real infrastructure into the job and company processing graphs.

This is the single place where infrastructure adapters are chosen for the
job/company context preparation and analysis workflows. Future providers
(Firecrawl, Jina Reader, ...) can be added here without touching application
or domain layers.
"""

from __future__ import annotations

from typing import Any

from ai.infrastructure.service import get_llm_service
from applications.infrastructure import (
    SQLAlchemyApplicationRepository,
    SQLAlchemyDocumentRepository,
)
from candidates.application.services.candidate_extract_service import CandidateExtractService
from candidates.domain.event_publisher import InMemoryEventCollector
from candidates.infrastructure import (
    SQLAlchemyCandidateProfileRepository,
    SQLAlchemyCandidateSourceRepository,
)
from cities.application.services.city_service import CityService
from cities.domain.event_publisher import InMemoryEventCollector as CityInMemoryEventCollector
from cities.infrastructure import SQLAlchemyCityRepository
from companies.application.services.company_matching_service import CompanyMatchingService
from companies.application.services.company_service import CompanyService
from companies.infrastructure.repositories.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
from companies.infrastructure.repositories.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
from companies.infrastructure.repositories.sa_company_repository import SQLAlchemyCompanyRepository
from jobs.application.services.job_service import JobService
from jobs.infrastructure.repositories.sa_job_analysis_repository import SQLAlchemyJobAnalysisRepository
from jobs.infrastructure.repositories.sa_job_company_repository import SQLAlchemyJobCompanyRepository
from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
from roadmaps.application.services.roadmap_service import RoadmapService
from roadmaps.domain.event_publisher import InMemoryEventCollector as RoadmapInMemoryEventCollector
from roadmaps.infrastructure import SQLAlchemyRoadmapRepository
from processing.application.workflows.candidate_processing import CandidateProcessingGraph
from processing.application.workflows.candidate_source_preparation import CandidateSourcePreparationGraph
from processing.application.workflows.company_analysis import CompanyAnalysisGraph
from processing.application.workflows.company_context_preparation import CompanyContextPreparationGraph
from processing.application.workflows.application_intelligence import ApplicationIntelligenceGraph
from processing.application.workflows.roadmap_generation import RoadmapGenerationGraph
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


def build_job_context_preparation_graph(session: Any, user_id: str = "") -> JobContextPreparationGraph:
    """Build the graph with production infrastructure adapters."""
    job_repo = SQLAlchemyJobRepository(session, user_id=user_id)
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


def build_job_analysis_graph(session: Any, user_id: str = "") -> JobAnalysisGraph:
    """Build the Job Analysis graph with production infrastructure adapters."""
    job_repo = SQLAlchemyJobRepository(session, user_id=user_id)
    job_service = JobService(job_repo)
    event_publisher = RedisProcessingEventPublisher()

    return JobAnalysisGraph(
        job_service=job_service,
        skill_repo=SQLAlchemySkillRepository(session, user_id=user_id),
        source_repo=SQLAlchemyCandidateSourceRepository(session),
        rule_repo=SQLAlchemyRuleRepository(session, user_id=user_id),
        job_repo=job_repo,
        summary_repo=SQLAlchemySummaryRepository(session),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        matching_service=CompanyMatchingService(SQLAlchemyCompanyRepository(session, user_id=user_id)),
        job_company_repo=SQLAlchemyJobCompanyRepository(session),
        llm_service=get_llm_service(),
        event_publisher=event_publisher,
        candidate_profile_repo=SQLAlchemyCandidateProfileRepository(session),
        city_service=_city_service(session, user_id),
    )


def _company_service(session: Any, user_id: str = "") -> CompanyService:
    return CompanyService(
        repository=SQLAlchemyCompanyRepository(session, user_id=user_id),
        intelligence_repository=SQLAlchemyCompanyIntelligenceRepository(session),
        link_repository=SQLAlchemyCompanyLinkRepository(session),
        city_service=_city_service(session, user_id),
    )


def _city_service(session: Any, user_id: str = "") -> CityService:
    return CityService(
        SQLAlchemyCityRepository(session, user_id=user_id),
        CityInMemoryEventCollector(),
    )


def build_company_context_preparation_graph(session: Any, user_id: str = "") -> CompanyContextPreparationGraph:
    """Build the Company context preparation graph (no LLM)."""
    fetcher = CompositeContentFetcher(
        [HTTPXContentFetcher(), PlaywrightContentFetcher()]
    )
    extractor = CompositeContentExtractor(
        [TrafilaturaContentExtractor(), BeautifulSoupContentExtractor()]
    )
    event_publisher = RedisProcessingEventPublisher()

    return CompanyContextPreparationGraph(
        company_service=_company_service(session, user_id),
        fetcher=fetcher,
        extractor=extractor,
        event_publisher=event_publisher,
    )


def build_company_analysis_graph(session: Any, user_id: str = "") -> CompanyAnalysisGraph:
    """Build the Company analysis graph with production infrastructure adapters."""
    return CompanyAnalysisGraph(
        company_service=_company_service(session, user_id),
        rule_repo=SQLAlchemyRuleRepository(session, user_id=user_id),
        llm_service=get_llm_service(),
        source_repo=SQLAlchemyCandidateSourceRepository(session),
        candidate_profile_repo=SQLAlchemyCandidateProfileRepository(session),
        event_publisher=RedisProcessingEventPublisher(),
    )


def build_candidate_source_preparation_graph(session: Any, user_id: str = "") -> CandidateSourcePreparationGraph:
    """Build the Candidate source preparation graph (no LLM)."""
    return CandidateSourcePreparationGraph(
        profile_repo=SQLAlchemyCandidateProfileRepository(session),
        source_repo=SQLAlchemyCandidateSourceRepository(session),
        event_publisher=RedisProcessingEventPublisher(),
    )


def build_candidate_processing_graph(session: Any, user_id: str = "") -> CandidateProcessingGraph:
    """Build the Candidate extraction/merge graph with production adapters."""
    extract_service = CandidateExtractService(
        profile_repo=SQLAlchemyCandidateProfileRepository(session),
        source_repo=SQLAlchemyCandidateSourceRepository(session),
        skill_repo=SQLAlchemySkillRepository(session, user_id=user_id),
        llm=get_llm_service(),
        event_publisher=InMemoryEventCollector(),
        city_service=_city_service(session, user_id),
    )
    return CandidateProcessingGraph(
        extract_service=extract_service,
        event_publisher=RedisProcessingEventPublisher(),
    )


def build_application_intelligence_graph(session: Any, user_id: str = "") -> ApplicationIntelligenceGraph:
    """Build the Application Intelligence graph with production adapters."""
    return ApplicationIntelligenceGraph(
        application_repo=SQLAlchemyApplicationRepository(session),
        job_service=JobService(SQLAlchemyJobRepository(session, user_id=user_id)),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        company_service=CompanyService(
            SQLAlchemyCompanyRepository(session, user_id=user_id),
            SQLAlchemyCompanyIntelligenceRepository(session),
            SQLAlchemyCompanyLinkRepository(session),
            city_service=_city_service(session, user_id),
        ),
        intelligence_repo=SQLAlchemyCompanyIntelligenceRepository(session),
        profile_repo=SQLAlchemyCandidateProfileRepository(session),
        document_repo=SQLAlchemyDocumentRepository(session),
        llm_service=get_llm_service(),
        event_publisher=RedisProcessingEventPublisher(),
    )


def build_roadmap_generation_graph(session: Any, user_id: str = "") -> RoadmapGenerationGraph:
    """Build the Roadmap Generation graph with production infrastructure adapters."""
    return RoadmapGenerationGraph(
        application_repo=SQLAlchemyApplicationRepository(session),
        job_service=JobService(SQLAlchemyJobRepository(session, user_id=user_id)),
        analysis_repo=SQLAlchemyJobAnalysisRepository(session),
        company_service=CompanyService(
            SQLAlchemyCompanyRepository(session, user_id=user_id),
            SQLAlchemyCompanyIntelligenceRepository(session),
            SQLAlchemyCompanyLinkRepository(session),
            city_service=_city_service(session, user_id),
        ),
        intelligence_repo=SQLAlchemyCompanyIntelligenceRepository(session),
        profile_repo=SQLAlchemyCandidateProfileRepository(session),
        roadmap_service=RoadmapService(
            SQLAlchemyRoadmapRepository(session, user_id=user_id),
            SQLAlchemySkillRepository(session, user_id=user_id),
            RoadmapInMemoryEventCollector(),
        ),
        llm_service=get_llm_service(),
        event_publisher=RedisProcessingEventPublisher(),
    )
