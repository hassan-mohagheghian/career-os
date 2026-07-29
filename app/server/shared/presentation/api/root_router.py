"""Root API router. Matches the exact paths the frontend expects.

Routes are organized by bounded context. Each context owns its
presentation/api/ layer with routers and schemas.
"""

import json
from datetime import datetime, UTC

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Bounded context routers — imported from their owning context's presentation layer
from jobs.presentation.api.jobs_router import router as jobs_router
from skills.presentation.api.skills_router import router as skills_router
from companies.presentation.api.companies_router import router as companies_router
from career.presentation.api.insights_router import router as insights_router
from resume.presentation.api.resumes_router import router as resumes_router
from skills.presentation.api.skill_roadmaps_router import router as skill_roadmaps_router
from career.presentation.api.rules_router import router as rules_router
from career.presentation.api.dashboard_router import router as dashboard_router
from shared.presentation.api.websocket_router import router as websocket_router

# DI dependencies — wired through bounded context infrastructure
from dependencies import get_session_sync, get_job_repo, get_skill_repo, get_company_repo, get_insight_repo, get_skill_roadmap_repo, get_skill_roadmap_progress_repo

# Bounded context infrastructure — for inline routes in this file
from jobs.infrastructure import SQLAlchemyJobRepository
from skills.infrastructure import SQLAlchemySkillRepository
from career.infrastructure import SQLAlchemyInsightRepository

api_router = APIRouter(prefix="/api")

# ── Feature routers ──────────────────────────────────────────────

api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(skills_router, prefix="/skills", tags=["skills"])
api_router.include_router(companies_router, prefix="/companies", tags=["companies"])
api_router.include_router(insights_router, prefix="/insights", tags=["insights"])
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(skill_roadmaps_router, prefix="/skill-roadmaps", tags=["skill-roadmaps"])
api_router.include_router(rules_router, prefix="/rules", tags=["rules"])
api_router.include_router(dashboard_router, prefix="", tags=["dashboard"])
api_router.include_router(websocket_router, tags=["websocket"])
# ── SSE router (compat) ──────────────────────────────────────────

@api_router.get("/api/pending/stream")
def pending_stream_compat():
    return {"status": "removed", "message": "Use WebSocket for real-time updates"}


@api_router.get("/api/pending-companies/stream")
def pending_companies_stream_compat():
    return {"status": "removed", "message": "Use WebSocket for real-time updates"}


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


@api_router.get("/linkedin")
def linkedin_compat():
    from resume.infrastructure import SQLAlchemyResumeRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemyResumeRepository(session)
        rows = repo.get_all()
        return [r for r in rows if r.get("id") == "original" or r.get("id", "").startswith("linkedin_")]
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


@api_router.get("/skills-intelligence/dashboard")
def skills_intel_dashboard_compat():
    session = get_session_sync()
    try:
        repo = SQLAlchemyInsightRepository(session)
        result = repo.get_section("skills")
        return result or {"skills": [], "summary": None}
    finally:
        session.close()


# ── Skill roadmap progress routes ───────────────────────────────

@api_router.get("/skill-roadmap-progress/all")
def skill_roadmap_progress_all():
    from skills.infrastructure import SQLAlchemySkillRoadmapProgressRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        return repo.get_all_aggregated()
    finally:
        session.close()


@api_router.get("/skill-roadmap-progress")
def skill_roadmap_progress_compat(skill: str = None):
    from skills.infrastructure import SQLAlchemySkillRoadmapProgressRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        if skill:
            return repo.get_by_skill(skill)
        else:
            return skill_roadmap_progress_all()
    finally:
        session.close()


@api_router.patch("/skill-roadmap-progress/{id}")
def toggle_roadmap_progress(id: int, data: dict = None):
    from skills.infrastructure import SQLAlchemySkillRoadmapProgressRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        result = repo.toggle(id, "")
        return result
    finally:
        session.close()


@api_router.put("/skill-roadmap-progress/{id}")
def update_roadmap_progress(id: int, data: dict = None):
    from skills.infrastructure import SQLAlchemySkillRoadmapProgressRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemySkillRoadmapProgressRepository(session)
        data = data or {}
        completed = 1 if data.get("completed") else 0
        return repo.set_completed(id, completed)
    finally:
        session.close()


@api_router.get("/skill-roadmap-jobs")
def skill_roadmap_jobs_compat(limit: int = 50):
    from skills.infrastructure import SQLAlchemySkillRoadmapJobRepository
    session = get_session_sync()
    try:
        repo = SQLAlchemySkillRoadmapJobRepository(session)
        return {"items": repo.get_all(limit)}
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

@api_router.post("/jobs/{num}/link-company")
def link_job_to_company(num: int, data: dict):
    session = get_session_sync()
    try:
        repo = SQLAlchemyJobRepository(session)
        company_id = data.get("company_id")
        if company_id:
            repo.update_fields(num, company_id=company_id)
            session.commit()
        return {"status": "linked"}
    finally:
        session.close()


@api_router.post("/companies/{id}/reprocess")
def reprocess_company(id: int, session: Session = Depends(get_session_sync)):
    from shared.infrastructure.config.queue import get_queue_manager
    from companies.infrastructure import SQLAlchemyCompanyRepository
    company_repo = SQLAlchemyCompanyRepository(session)
    company = company_repo.get_by_id(id)
    if not company:
        return {"error": "Not found"}
    company_repo.update_fields(id, status='queued', error=None, updated_at=datetime.now(UTC).isoformat())
    session.commit()
    get_queue_manager().enqueue(id, entity_type='company')
    return {"status": "queued"}


# ── Pending jobs compat routes ──────────────────────────────────

@api_router.get("/pending")
def list_pending_jobs(session: Session = Depends(get_session_sync)):
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    repo = SQLAlchemyPendingRepository(session)
    return repo.list_pending("pending_jobs")


@api_router.post("/pending")
def create_pending_job(data: dict, session: Session = Depends(get_session_sync)):
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    repo = SQLAlchemyPendingRepository(session)
    return repo.create(data, "pending_jobs")


@api_router.post("/pending/process-all")
def process_all_pending_jobs(session: Session = Depends(get_session_sync)):
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    from shared.infrastructure.config.queue import get_queue_manager
    repo = SQLAlchemyPendingRepository(session)
    items = repo.list_pending("pending_jobs")
    for item in items:
        get_queue_manager().enqueue(item['num'], entity_type='job')
    return {"status": "queued", "count": len(items)}


@api_router.get("/pending/{item_id}")
def get_pending_job(item_id: str, session: Session = Depends(get_session_sync)):
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    from fastapi.responses import JSONResponse
    repo = SQLAlchemyPendingRepository(session)
    result = repo.get_by_id(item_id, "pending_jobs")
    if result is None:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return result


@api_router.delete("/pending/{item_id}")
def cancel_pending_job(item_id: str, session: Session = Depends(get_session_sync)):
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    from shared.infrastructure.config.queue import get_queue_manager
    repo = SQLAlchemyPendingRepository(session)
    item = repo.get_by_id(item_id, "pending_jobs")
    if not item:
        return {"error": "Not found"}
    get_queue_manager().cancel_item(int(item_id), entity_type='job')
    repo.update_status(str(item_id), "cancelled", "pending_jobs")
    return {"status": "cancelled"}


@api_router.post("/pending/{item_id}/reset")
def reset_pending_job(item_id: int, session: Session = Depends(get_session_sync)):
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    from shared.infrastructure.config.queue import get_queue_manager
    repo = SQLAlchemyPendingRepository(session)
    get_queue_manager().reset_item(item_id, entity_type='job')
    repo.reset_steps(item_id, version=2)
    return {"status": "reset"}


@api_router.post("/pending/{item_id}/process")
def process_pending_job(item_id: int):
    from shared.infrastructure.config.queue import get_queue_manager
    get_queue_manager().enqueue(item_id, entity_type='job')
    return {"status": "queued"}


# ── Pending companies compat routes ─────────────────────────────

@api_router.get("/pending-companies")
def list_pending_companies(session: Session = Depends(get_session_sync)):
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    repo = SQLAlchemyPendingRepository(session)
    return repo.list_pending("pending_companies")


@api_router.post("/pending-companies")
def create_pending_company(data: dict, session: Session = Depends(get_session_sync)):
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    repo = SQLAlchemyPendingRepository(session)
    return repo.create(data, "pending_companies")


@api_router.post("/pending-companies/queue-all")
def queue_all_pending_companies(session: Session = Depends(get_session_sync)):
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    from shared.infrastructure.config.queue import get_queue_manager
    repo = SQLAlchemyPendingRepository(session)
    items = repo.list_pending("pending_companies")
    for item in items:
        get_queue_manager().enqueue(item['id'], entity_type='company')
    return {"status": "queued", "count": len(items)}


@api_router.get("/pending-companies/{item_id}")
def get_pending_company(item_id: str, session: Session = Depends(get_session_sync)):
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    from fastapi.responses import JSONResponse
    repo = SQLAlchemyPendingRepository(session)
    result = repo.get_by_id(str(item_id), "pending_companies")
    if result is None:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return result


@api_router.delete("/pending-companies/{item_id}")
def cancel_pending_company(item_id: str, session: Session = Depends(get_session_sync)):
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    from shared.infrastructure.config.queue import get_queue_manager
    from fastapi.responses import JSONResponse
    repo = SQLAlchemyPendingRepository(session)
    result = repo.get_by_id(str(item_id), "pending_companies")
    if not result:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    repo.update_status(str(item_id), "cancelled", "pending_companies")
    get_queue_manager().cancel_item(int(item_id), entity_type='company')
    return {"status": "cancelled"}


@api_router.post("/pending-companies/{item_id}/notes")
def add_pending_company_notes(item_id: str, data: dict = None, session: Session = Depends(get_session_sync)):
    import json
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    from fastapi.responses import JSONResponse
    repo = SQLAlchemyPendingRepository(session)
    item = repo.get_by_id(str(item_id), "pending_companies")
    if not item:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    existing_notes = json.loads(item.get('notes', '[]'))
    new_notes = (data or {}).get('notes', [])
    notes = existing_notes + new_notes
    repo.update_fields(int(item_id), table="pending_companies", notes=json.dumps(notes))
    return {"status": "updated", "notes": notes}


@api_router.post("/pending-companies/{item_id}/links")
def add_pending_company_links(item_id: str, data: dict = None, session: Session = Depends(get_session_sync)):
    import json
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    from fastapi.responses import JSONResponse
    repo = SQLAlchemyPendingRepository(session)
    item = repo.get_by_id(str(item_id), "pending_companies")
    if not item:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    new_links = (data or {}).get('links', [])
    repo.update_fields(int(item_id), table="pending_companies", notes=json.dumps(new_links))
    return {"status": "updated", "links": new_links}


@api_router.post("/pending-companies/{item_id}/process")
def process_pending_company(item_id: int):
    from shared.infrastructure.config.queue import get_queue_manager
    get_queue_manager().enqueue(item_id, entity_type='company')
    return {"status": "queued"}


# ── Resume compat routes ────────────────────────────────────────

@api_router.get("/resumes/active-generations")
def active_generations_compat(session: Session = Depends(get_session_sync)):
    return []
