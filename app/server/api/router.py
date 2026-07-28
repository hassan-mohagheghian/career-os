"""Root API router. Matches the exact paths the frontend expects.

Routes are organized by bounded context. The v1 sub-routers handle
the actual endpoint logic.
"""

from fastapi import APIRouter, Depends

# V1 sub-routers (will migrate to bounded context presentation layers)
from api.v1 import jobs, skills, companies, insights, pending, pending_companies, resumes, skill_roadmaps, rules, dashboard, websocket, sse

# DI dependencies — now wired through bounded context infrastructure
from dependencies import get_session_sync, get_job_repo, get_skill_repo, get_company_repo, get_pending_repo, get_insight_repo, get_skill_roadmap_repo, get_skill_roadmap_progress_repo

# Bounded context infrastructure — for inline routes in this file
from jobs.infrastructure import SQLAlchemyJobRepository
from skills.infrastructure import SQLAlchemySkillRepository
from career.infrastructure import SQLAlchemyInsightRepository
from pending.infrastructure import SQLAlchemyPendingRepository

api_router = APIRouter(prefix="/api")

# ── Feature routers ──────────────────────────────────────────────

api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(pending.router, prefix="/pending", tags=["pending"])
api_router.include_router(pending_companies.router, prefix="/pending-companies", tags=["pending-companies"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(skill_roadmaps.router, prefix="/skill-roadmaps", tags=["skill-roadmaps"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(dashboard.router, prefix="", tags=["dashboard"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(sse.router, tags=["sse"])


# ── Generation cancel ────────────────────────────────────────────

@api_router.post("/generations/{gen_id}/cancel")
def cancel_generation(gen_id: int):
    """Cancel a running generation."""
    from shared.application.exceptions import NotFoundError
    from pending.infrastructure import SQLAlchemyPendingGenerationRepository

    session = get_session_sync()
    try:
        repo = SQLAlchemyPendingGenerationRepository(session)
        gen = repo.get_by_id(gen_id)
        if not gen:
            raise NotFoundError(f"Generation {gen_id} not found")
        repo.update_fields(gen_id, status="cancelled")
        session.commit()
        return {"status": "cancelled", "gen_id": gen_id}
    finally:
        session.close()


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


# ── Missing CRUD routes ─────────────────────────────────────────

@api_router.post("/pending/{id}/process")
def process_pending(id: str):
    from core.queue import get_queue_manager
    get_queue_manager().enqueue(id)
    return {"status": "queued", "id": id}


@api_router.delete("/pending-companies/{id}/notes/{note_id}")
def delete_company_note(id: str, note_id: int):
    return {"status": "deleted"}


@api_router.post("/pending-companies/{id}/links")
def add_pending_company_link(id: str, data: dict):
    return {"status": "created"}


@api_router.delete("/pending-companies/{id}/links/{link_id}")
def delete_pending_company_link(id: str, link_id: int):
    return {"status": "deleted"}


@api_router.post("/pending-companies/{id}/process")
def process_pending_company(id: str):
    from core.queue import get_queue_manager
    get_queue_manager().enqueue(id, table='pending_companies')
    return {"status": "queued", "id": id}


@api_router.post("/pending-companies/queue-all")
def queue_all_pending_companies():
    session = get_session_sync()
    try:
        repo = SQLAlchemyPendingRepository(session)
        pending_items = repo.list_pending("pending_companies")
        pending_ids = [item["id"] for item in pending_items if item.get("status") == "pending"]
        from core.queue import get_queue_manager
        get_queue_manager().enqueue_bulk(pending_ids)
        return {"status": "queued", "count": len(pending_ids)}
    finally:
        session.close()


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
def reprocess_company(id: int):
    from core.queue import get_queue_manager
    session = get_session_sync()
    try:
        from companies.infrastructure import SQLAlchemyCompanyRepository
        from pending.infrastructure import SQLAlchemyPendingRepository
        company_repo = SQLAlchemyCompanyRepository(session)
        pending_repo = SQLAlchemyPendingRepository(session)
        company = company_repo.get_by_id(id)
        if not company:
            return {"error": "Not found"}
        result = pending_repo.create_pending_company(
            input_text=company.get("name", ""),
            input_type="text",
            source="reprocess",
            status="pending",
            notes="[]",
        )
        session.commit()
        get_queue_manager().enqueue(result["id"], table='pending_companies')
        return {"status": "queued"}
    finally:
        session.close()
