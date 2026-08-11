"""Root API router. Matches the exact paths the frontend expects.

Routes are organized by bounded context. Each context owns its
presentation/api/ layer with routers and schemas.
"""

import json
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

# Bounded context routers — imported from their owning context's presentation layer
from skills.presentation.api.skills_router import router as skills_router
from companies.presentation.api.companies_router import router as companies_router

from rules.presentation.api.rules_router import router as rules_router
from shared.presentation.api.dashboard_router import router as dashboard_router
from ai.presentation.api.llm_configurations_router import router as llm_configurations_router
from processing.presentation.api.process_router import router as process_router
from processing.presentation.api.executions_router import router as executions_router
from candidates.presentation.api.candidates_router import router as candidates_router
from applications.presentation.api.applications_router import router as applications_router

# DI dependencies — wired through bounded context infrastructure
from dependencies import get_session_sync, get_job_repo, get_skill_repo, get_company_repo

# Bounded context infrastructure — for inline routes in this file
from jobs.infrastructure import SQLAlchemyJobRepository
from skills.infrastructure import SQLAlchemySkillRepository


api_router = APIRouter(prefix="/api")

# ── V2 routers (registered before legacy to prevent path conflicts) ──

from jobs.presentation.api.jobs_v2_router import router as jobs_v2_router
api_router.include_router(jobs_v2_router, prefix="/jobs", tags=["jobs-v2"])

from companies.presentation.api.companies_v2_router import router as companies_v2_router
api_router.include_router(companies_v2_router, prefix="/companies", tags=["companies-v2"])

# ── Feature routers ──────────────────────────────────────────────

api_router.include_router(skills_router, prefix="/skills", tags=["skills"])
api_router.include_router(companies_router, prefix="/companies", tags=["companies"])

api_router.include_router(rules_router, prefix="/rules", tags=["rules"])
api_router.include_router(dashboard_router, prefix="", tags=["dashboard"])
api_router.include_router(llm_configurations_router, prefix="/llm-configurations", tags=["llm-configurations"])
api_router.include_router(process_router, prefix="/jobs", tags=["processing"])
api_router.include_router(executions_router, prefix="/processing", tags=["processing"])

# ── Candidate Profile ────────────────────────────────────────────

api_router.include_router(candidates_router, prefix="/candidates", tags=["candidates"])
api_router.include_router(applications_router, prefix="/applications", tags=["applications"])

# ── Flask compat routes ─────────────────────────────────────────

@api_router.get("/summaries")
def summaries_compat():
    from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemySummaryRepository(session)
        return repo.get_all()
    finally:
        session.close()


@api_router.get("/tech-stack")
def tech_stack_compat():
    session = get_session_sync()
    try:
        repo = SQLAlchemySkillRepository(session)
        return repo.list_visible()
    finally:
        session.close()


# ── Skill relationships compat routes ───────────────────────────

@api_router.get("/skill-relationships/{skill_name}")
def get_skill_relationships_compat(skill_name: str):
    session = get_session_sync()
    try:
        repo = SQLAlchemySkillRepository(session)
        return repo.get_relationships(skill_name)
    finally:
        session.close()


@api_router.post("/skill-relationships")
def create_skill_relationship_compat(data: dict):
    from shared.application.exceptions import ConflictError
    session = get_session_sync()
    try:
        repo = SQLAlchemySkillRepository(session)
        success = repo.create_relationship(data)
        if not success:
            raise ConflictError("Relationship already exists")
        return {"status": "created"}
    finally:
        session.close()


@api_router.delete("/skill-relationships/{id}")
def delete_skill_relationship_compat(id: int):
    session = get_session_sync()
    try:
        repo = SQLAlchemySkillRepository(session)
        repo.delete_relationship(id)
        return {"status": "deleted"}
    finally:
        session.close()


# ── Job-Company link ─────────────────────────────────────────────

@api_router.post("/jobs/{job_id}/link-company")
def link_job_to_company(job_id: str, data: dict):
    session = get_session_sync()
    try:
        repo = SQLAlchemyJobRepository(session)
        company_id = data.get("company_id")
        if company_id:
            repo.update_fields(job_id, company_id=company_id)
            session.commit()
        return {"status": "linked"}
    finally:
        session.close()


@api_router.post("/companies/{id}/reprocess")
def reprocess_company(id: str, session: Session = Depends(get_session_sync)):
    from companies.infrastructure import SQLAlchemyCompanyRepository
    from processing.infrastructure import SQLAlchemyProcessingExecutionRepository
    from processing.application.services.execution_actions import ExecutionActionService

    company_repo = SQLAlchemyCompanyRepository(session)
    company = company_repo.get_by_id(id)
    if not company:
        return {"error": "Not found"}

    exec_repo = SQLAlchemyProcessingExecutionRepository(session)
    result = ExecutionActionService(exec_repo).reprocess("company", id)

    company_repo.update_fields(id, status="queued", error=None, updated_at=datetime.now(UTC).isoformat())
    session.commit()
    return {"status": "queued", "execution_id": result["execution_id"]}



