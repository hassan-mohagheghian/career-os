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


# ── Pending Context Dependencies (DEPRECATED - will be removed) ──

def get_pending_repo(session: Session = Depends(get_session)):
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    return SQLAlchemyJobRepository(session)
