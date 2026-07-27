"""FastAPI dependency injection functions.

All database access goes through SQLAlchemy repositories.
Legacy sqlite3 dependencies are removed.
"""

from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session


# ── SQLAlchemy Session Dependency ─────────────────────────────────

def get_session() -> Generator[Session, None, None]:
    """Get a SQLAlchemy session for the request lifetime.

    Yields a Session and auto-commits on success, rolls back on error.
    """
    from infrastructure.database.sqlalchemy_config import SessionLocal
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_sync() -> Session:
    """Get a synchronous SQLAlchemy session (for non-async contexts)."""
    from infrastructure.database.sqlalchemy_config import SessionLocal
    return SessionLocal()


# ── SQLAlchemy Repository Dependencies ───────────────────────────

def get_job_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
    return SQLAlchemyJobRepository(session)


def get_skill_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
    return SQLAlchemySkillRepository(session)


def get_company_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
    return SQLAlchemyCompanyRepository(session)


def get_pending_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    return SQLAlchemyPendingRepository(session)


def get_insight_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_insight_repository import SQLAlchemyInsightRepository
    return SQLAlchemyInsightRepository(session)


def get_preference_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_preference_repository import SQLAlchemyPreferenceRepository
    return SQLAlchemyPreferenceRepository(session)


def get_summary_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_summary_repository import SQLAlchemySummaryRepository
    return SQLAlchemySummaryRepository(session)


def get_resume_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_resume_repository import SQLAlchemyResumeRepository
    return SQLAlchemyResumeRepository(session)


def get_company_link_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
    return SQLAlchemyCompanyLinkRepository(session)


def get_company_intelligence_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
    return SQLAlchemyCompanyIntelligenceRepository(session)


def get_pending_generation_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
    return SQLAlchemyPendingGenerationRepository(session)


def get_career_insight_run_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
    return SQLAlchemyCareerInsightRunRepository(session)


def get_career_insight_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_career_insight_repository import SQLAlchemyCareerInsightRepository
    return SQLAlchemyCareerInsightRepository(session)


def get_tech_learning_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_tech_learning_repository import SQLAlchemyTechLearningRepository
    return SQLAlchemyTechLearningRepository(session)


def get_skill_alias_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_skill_alias_repository import SQLAlchemySkillAliasRepository
    return SQLAlchemySkillAliasRepository(session)


def get_skill_relationship_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_skill_relationship_repository import SQLAlchemySkillRelationshipRepository
    return SQLAlchemySkillRelationshipRepository(session)


def get_skill_roadmap_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
    return SQLAlchemySkillRoadmapRepository(session)


def get_skill_roadmap_progress_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
    return SQLAlchemySkillRoadmapProgressRepository(session)


def get_skill_roadmap_job_repo(session: Session = Depends(get_session)):
    from infrastructure.database.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
    return SQLAlchemySkillRoadmapJobRepository(session)


# ── Legacy aliases (kept for backward compat during migration) ───

get_db = get_session
get_db_sync = get_session_sync
