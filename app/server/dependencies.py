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


def get_skill_alias_repo(session: Session = Depends(get_session)):
    from skills.infrastructure import SQLAlchemySkillAliasRepository
    return SQLAlchemySkillAliasRepository(session)


def get_skill_relationship_repo(session: Session = Depends(get_session)):
    from skills.infrastructure import SQLAlchemySkillRelationshipRepository
    return SQLAlchemySkillRelationshipRepository(session)


def get_skill_roadmap_repo(session: Session = Depends(get_session)):
    from skills.infrastructure import SQLAlchemySkillRoadmapRepository
    return SQLAlchemySkillRoadmapRepository(session)


def get_skill_roadmap_progress_repo(session: Session = Depends(get_session)):
    from skills.infrastructure import SQLAlchemySkillRoadmapProgressRepository
    return SQLAlchemySkillRoadmapProgressRepository(session)


def get_skill_roadmap_job_repo(session: Session = Depends(get_session)):
    from skills.infrastructure import SQLAlchemySkillRoadmapJobRepository
    return SQLAlchemySkillRoadmapJobRepository(session)


# ── Career Context Dependencies ───────────────────────────────────

def get_insight_repo(session: Session = Depends(get_session)):
    from career.infrastructure import SQLAlchemyInsightRepository
    return SQLAlchemyInsightRepository(session)


def get_career_insight_repo(session: Session = Depends(get_session)):
    from career.infrastructure import SQLAlchemyCareerInsightRepository
    return SQLAlchemyCareerInsightRepository(session)


def get_career_insight_run_repo(session: Session = Depends(get_session)):
    from career.infrastructure import SQLAlchemyCareerInsightRunRepository
    return SQLAlchemyCareerInsightRunRepository(session)


def get_preference_repo(session: Session = Depends(get_session)):
    from career.infrastructure import SQLAlchemyPreferenceRepository
    return SQLAlchemyPreferenceRepository(session)


def get_tech_learning_repo(session: Session = Depends(get_session)):
    from skills.infrastructure import SQLAlchemyTechLearningRepository
    return SQLAlchemyTechLearningRepository(session)


# ── Resume Context Dependencies ───────────────────────────────────

def get_resume_repo(session: Session = Depends(get_session)):
    from resume.infrastructure import SQLAlchemyResumeRepository
    return SQLAlchemyResumeRepository(session)


def get_summary_repo(session: Session = Depends(get_session)):
    from jobs.infrastructure import SQLAlchemyJobRepository
    # Summary uses the same repository as jobs during migration
    from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
    return SQLAlchemySummaryRepository(session)


# ── Pending Context Dependencies ──────────────────────────────────

def get_pending_repo(session: Session = Depends(get_session)):
    from pending.infrastructure import SQLAlchemyPendingRepository
    return SQLAlchemyPendingRepository(session)


def get_pending_generation_repo(session: Session = Depends(get_session)):
    from pending.infrastructure import SQLAlchemyPendingGenerationRepository
    return SQLAlchemyPendingGenerationRepository(session)
