"""FastAPI dependency injection functions.

All database access goes through bounded context infrastructure layers.
Repository factories are organized by bounded context.
"""

from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from shared.infrastructure.database.session import get_session, get_session_sync


# ── Re-export shared session dependencies ──────────────────────────
# These are the canonical session factories — all bounded contexts use them.
get_session = get_session
get_session_sync = get_session_sync


# ── Jobs Context Dependencies ─────────────────────────────────────

def get_job_repo(session: Session = Depends(get_session)):
    from jobs.infrastructure import SQLAlchemyJobRepository
    return SQLAlchemyJobRepository(session)


# ── Companies Context Dependencies ────────────────────────────────

def get_company_repo(session: Session = Depends(get_session)):
    from companies.infrastructure import SQLAlchemyCompanyRepository
    return SQLAlchemyCompanyRepository(session)


def get_company_link_repo(session: Session = Depends(get_session)):
    from companies.infrastructure import SQLAlchemyCompanyLinkRepository
    return SQLAlchemyCompanyLinkRepository(session)


def get_company_intelligence_repo(session: Session = Depends(get_session)):
    from companies.infrastructure import SQLAlchemyCompanyIntelligenceRepository
    return SQLAlchemyCompanyIntelligenceRepository(session)


# ── Skills Context Dependencies ───────────────────────────────────

def get_skill_repo(session: Session = Depends(get_session)):
    from skills.infrastructure import SQLAlchemySkillRepository
    return SQLAlchemySkillRepository(session)


def get_skill_category_service(repo=Depends(get_skill_repo)):
    from skills.domain.event_publisher import InMemoryEventCollector
    from skills.application.use_cases.skill_category_service import SkillCategoryService
    return SkillCategoryService(repo, InMemoryEventCollector())


def get_skill_normalization_service(repo=Depends(get_skill_repo)):
    from skills.domain.event_publisher import InMemoryEventCollector
    from skills.application.use_cases.skill_normalization_service import SkillNormalizationService
    return SkillNormalizationService(repo, InMemoryEventCollector())


def get_skill_alias_repo(session: Session = Depends(get_session)):
    from skills.infrastructure import SQLAlchemySkillAliasRepository
    return SQLAlchemySkillAliasRepository(session)


def get_skill_relationship_repo(session: Session = Depends(get_session)):
    from skills.infrastructure import SQLAlchemySkillRelationshipRepository
    return SQLAlchemySkillRelationshipRepository(session)


# ── Rules Context Dependencies ───────────────────────────────────

def get_rule_repo(session: Session = Depends(get_session)):
    from rules.infrastructure import SQLAlchemyRuleRepository
    return SQLAlchemyRuleRepository(session)


# ── Candidates Context Dependencies ──────────────────────────────

def get_candidate_repo(session: Session = Depends(get_session)):
    from candidates.infrastructure import SQLAlchemyCandidateRepository
    return SQLAlchemyCandidateRepository(session)


def get_candidate_profile_repo(session: Session = Depends(get_session)):
    from candidates.infrastructure import SQLAlchemyCandidateProfileRepository
    return SQLAlchemyCandidateProfileRepository(session)


def get_candidate_source_repo(session: Session = Depends(get_session)):
    from candidates.infrastructure import SQLAlchemyCandidateSourceRepository
    return SQLAlchemyCandidateSourceRepository(session)


def get_candidate_extract_service(
    profile_repo=Depends(get_candidate_profile_repo),
    source_repo=Depends(get_candidate_source_repo),
    skill_repo=Depends(get_skill_repo),
):
    from candidates.application.services.candidate_extract_service import CandidateExtractService
    return CandidateExtractService(
        profile_repo=profile_repo,
        source_repo=source_repo,
        skill_repo=skill_repo,
    )


# ── Jobs Context Dependencies ─────────────────────────────────────

def get_summary_repo(session: Session = Depends(get_session)):
    from jobs.infrastructure import SQLAlchemyJobRepository
    # Summary uses the same repository as jobs during migration
    from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
    return SQLAlchemySummaryRepository(session)


def get_job_analysis_repo(session: Session = Depends(get_session)):
    from jobs.infrastructure.repositories.sa_job_analysis_repository import SQLAlchemyJobAnalysisRepository
    return SQLAlchemyJobAnalysisRepository(session)


def get_job_company_repo(session: Session = Depends(get_session)):
    from jobs.infrastructure.repositories.sa_job_company_repository import SQLAlchemyJobCompanyRepository
    return SQLAlchemyJobCompanyRepository(session)


# ── Processing Context Dependencies ──────────────────────────────

def get_processing_execution_repo(session: Session = Depends(get_session)):
    from processing.infrastructure import SQLAlchemyProcessingExecutionRepository
    return SQLAlchemyProcessingExecutionRepository(session)


# ── Applications Context Dependencies ────────────────────────────

def get_application_repo(session: Session = Depends(get_session)):
    from applications.infrastructure import SQLAlchemyApplicationRepository
    return SQLAlchemyApplicationRepository(session)


def get_status_event_repo(session: Session = Depends(get_session)):
    from applications.infrastructure import SQLAlchemyStatusEventRepository
    return SQLAlchemyStatusEventRepository(session)


def get_follow_up_repo(session: Session = Depends(get_session)):
    from applications.infrastructure import SQLAlchemyFollowUpRepository
    return SQLAlchemyFollowUpRepository(session)


def get_document_repo(session: Session = Depends(get_session)):
    from applications.infrastructure import SQLAlchemyDocumentRepository
    return SQLAlchemyDocumentRepository(session)


def get_note_repo(session: Session = Depends(get_session)):
    from applications.infrastructure import SQLAlchemyNoteRepository
    return SQLAlchemyNoteRepository(session)


def get_application_service(
    application_repo=Depends(get_application_repo),
    status_event_repo=Depends(get_status_event_repo),
):
    from applications.application.services.application_service import ApplicationService
    from applications.domain.event_publisher import InMemoryEventCollector
    return ApplicationService(application_repo, InMemoryEventCollector(), status_event_repo)


def get_status_event_service(
    status_event_repo=Depends(get_status_event_repo),
    application_repo=Depends(get_application_repo),
):
    from applications.application.services.status_event_service import StatusEventService
    from applications.domain.event_publisher import InMemoryEventCollector
    return StatusEventService(status_event_repo, application_repo, InMemoryEventCollector())


def get_follow_up_service(
    follow_up_repo=Depends(get_follow_up_repo),
    application_repo=Depends(get_application_repo),
):
    from applications.application.services.follow_up_service import FollowUpService
    from applications.domain.event_publisher import InMemoryEventCollector
    return FollowUpService(follow_up_repo, application_repo, InMemoryEventCollector())


def get_document_service(
    document_repo=Depends(get_document_repo),
):
    from applications.application.services.document_service import DocumentService
    from applications.domain.event_publisher import InMemoryEventCollector
    return DocumentService(document_repo, InMemoryEventCollector())


def get_note_service(
    note_repo=Depends(get_note_repo),
    application_repo=Depends(get_application_repo),
):
    from applications.application.services.note_service import NoteService
    from applications.domain.event_publisher import InMemoryEventCollector
    return NoteService(note_repo, application_repo, InMemoryEventCollector())


# ── Roadmaps Context Dependencies ────────────────────────────────

def get_roadmap_repo(session: Session = Depends(get_session)):
    from roadmaps.infrastructure import SQLAlchemyRoadmapRepository
    return SQLAlchemyRoadmapRepository(session)


def get_roadmap_service(
    roadmap_repo=Depends(get_roadmap_repo),
    skill_repo=Depends(get_skill_repo),
):
    from roadmaps.application.services.roadmap_service import RoadmapService
    from roadmaps.domain.event_publisher import InMemoryEventCollector
    return RoadmapService(roadmap_repo, skill_repo, InMemoryEventCollector())


# ── Placeholders Context Dependencies ─────────────────────────────

def get_placeholder_repo(session: Session = Depends(get_session)):
    from placeholders.infrastructure import SQLAlchemyPlaceholderRepository
    return SQLAlchemyPlaceholderRepository(session)


def get_placeholder_service(
    placeholder_repo=Depends(get_placeholder_repo),
):
    from placeholders.application.services.placeholder_service import PlaceholderService
    from placeholders.domain.event_publisher import InMemoryEventCollector
    return PlaceholderService(placeholder_repo, InMemoryEventCollector())


# ── Cities Context Dependencies ─────────────────────────────────

def get_city_repo(session: Session = Depends(get_session)):
    from cities.infrastructure import SQLAlchemyCityRepository
    return SQLAlchemyCityRepository(session)


def get_city_service(
    city_repo=Depends(get_city_repo),
):
    from cities.application.services.city_service import CityService
    from cities.domain.event_publisher import InMemoryEventCollector
    return CityService(city_repo, InMemoryEventCollector())


# ── Pending Context Dependencies (DEPRECATED - will be removed) ──

def get_pending_repo(session: Session = Depends(get_session)):
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    return SQLAlchemyJobRepository(session)
