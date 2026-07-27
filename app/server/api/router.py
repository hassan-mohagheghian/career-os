"""Root API router. Matches the exact paths the frontend expects."""

from fastapi import APIRouter, Query

from api.v1 import jobs, skills, companies, insights, pending, pending_companies, resumes, skill_roadmaps, rules, dashboard, websocket, sse
from dependencies import get_db_sync

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
    from exceptions import NotFoundError
    db = get_db_sync()
    try:
        row = db.execute("SELECT id, status FROM pending_generations WHERE id=?", (gen_id,)).fetchone()
        if not row:
            raise NotFoundError(f"Generation {gen_id} not found")
        db.execute("UPDATE pending_generations SET status='cancelled' WHERE id=?", (gen_id,))
        db.commit()
        return {"status": "cancelled", "gen_id": gen_id}
    finally:
        db.close()


# ── Flask compat routes ─────────────────────────────────────────

@api_router.get("/summaries")
def summaries_compat():
    db = get_db_sync()
    try:
        grade_order = "CASE score WHEN 'A++' THEN 7 WHEN 'A+' THEN 6 WHEN 'A' THEN 5 WHEN 'B' THEN 4 WHEN 'C' THEN 3 WHEN 'D' THEN 2 WHEN 'E' THEN 1 ELSE 0 END"
        rows = db.execute(f"SELECT * FROM summaries ORDER BY {grade_order} DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


@api_router.get("/linkedin")
def linkedin_compat():
    db = get_db_sync()
    try:
        rows = db.execute("SELECT * FROM resumes WHERE id='original' OR id LIKE 'linkedin_%'").fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


@api_router.get("/tech-stack")
def tech_stack_compat():
    from infrastructure.database.skill_repository import SkillRepository
    db = get_db_sync()
    try:
        return SkillRepository(db).list_visible()
    finally:
        db.close()


@api_router.get("/skills-intelligence/dashboard")
def skills_intel_dashboard_compat():
    from infrastructure.database.insight_repository import InsightRepository
    db = get_db_sync()
    try:
        result = InsightRepository(db).get_section("skills")
        return result or {"skills": [], "summary": None}
    finally:
        db.close()


# ── Skill roadmap progress routes ───────────────────────────────

@api_router.get("/skill-roadmap-progress/all")
def skill_roadmap_progress_all():
    db = get_db_sync()
    try:
        total_rows = db.execute(
            "SELECT skill_name, COUNT(*) as total_count FROM skill_roadmaps GROUP BY skill_name"
        ).fetchall()
        completed_rows = db.execute(
            "SELECT skill_name, COUNT(*) as completed_count FROM skill_roadmap_progress WHERE completed=1 GROUP BY skill_name"
        ).fetchall()
        completed_map = {r["skill_name"]: r["completed_count"] for r in completed_rows}

        progress_rows = db.execute("SELECT skill_name, roadmap_id, completed FROM skill_roadmap_progress").fetchall()
        checked_map = {}
        for r in progress_rows:
            sname = r["skill_name"]
            if sname not in checked_map:
                checked_map[sname] = {}
            checked_map[sname][r["roadmap_id"]] = r["completed"]

        result = {}
        for r in total_rows:
            sname = r["skill_name"]
            tot = r["total_count"]
            comp = completed_map.get(sname, 0)
            pct = round((comp / tot) * 100) if tot > 0 else 0
            result[sname] = {
                "total": tot,
                "completed": comp,
                "pct": pct,
                "checked": checked_map.get(sname, {}),
            }
        return result
    finally:
        db.close()


@api_router.get("/skill-roadmap-progress")
def skill_roadmap_progress_compat(skill: str = Query(None)):
    db = get_db_sync()
    try:
        if skill:
            rows = db.execute("SELECT * FROM skill_roadmap_progress WHERE LOWER(skill_name)=LOWER(?)", (skill,)).fetchall()
            return {r["roadmap_id"]: r["completed"] for r in rows}
        else:
            return skill_roadmap_progress_all()
    finally:
        db.close()


@api_router.patch("/skill-roadmap-progress/{id}")
def toggle_roadmap_progress(id: int, data: dict = None, db=None):
    db = get_db_sync()
    try:
        row = db.execute(
            "SELECT * FROM skill_roadmap_progress WHERE id=? OR roadmap_id=?", 
            (id, id)
        ).fetchone()
        
        if row:
            new_completed = 0 if row["completed"] else 1
            db.execute(
                "UPDATE skill_roadmap_progress SET completed=?, updated_at=datetime('now') WHERE id=?", 
                (new_completed, row["id"])
            )
            db.commit()
            updated_row = db.execute("SELECT * FROM skill_roadmap_progress WHERE id=?", (row["id"],)).fetchone()
            return dict(updated_row)
        else:
            rm_row = db.execute("SELECT skill_name FROM skill_roadmaps WHERE id=?", (id,)).fetchone()
            skill_name = rm_row["skill_name"] if rm_row else ""
            cur = db.execute(
                "INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, 1)",
                (id, skill_name)
            )
            db.commit()
            new_row = db.execute("SELECT * FROM skill_roadmap_progress WHERE id=?", (cur.lastrowid,)).fetchone()
            return dict(new_row)
    finally:
        db.close()


@api_router.put("/skill-roadmap-progress/{id}")
def update_roadmap_progress(id: int, data: dict = None):
    db = get_db_sync()
    try:
        data = data or {}
        completed = 1 if data.get("completed") else 0
        
        row = db.execute(
            "SELECT * FROM skill_roadmap_progress WHERE id=? OR roadmap_id=?", 
            (id, id)
        ).fetchone()

        if row:
            db.execute(
                "UPDATE skill_roadmap_progress SET completed=?, updated_at=datetime('now') WHERE id=?", 
                (completed, row["id"])
            )
            db.commit()
            updated_row = db.execute("SELECT * FROM skill_roadmap_progress WHERE id=?", (row["id"],)).fetchone()
            return dict(updated_row)
        else:
            rm_row = db.execute("SELECT skill_name FROM skill_roadmaps WHERE id=?", (id,)).fetchone()
            skill_name = rm_row["skill_name"] if rm_row else ""
            
            cur = db.execute(
                "INSERT INTO skill_roadmap_progress (roadmap_id, skill_name, completed) VALUES (?, ?, ?)",
                (id, skill_name, completed)
            )
            db.commit()
            new_row = db.execute("SELECT * FROM skill_roadmap_progress WHERE id=?", (cur.lastrowid,)).fetchone()
            return dict(new_row)
    finally:
        db.close()


@api_router.get("/skill-roadmap-jobs")
def skill_roadmap_jobs_compat(limit: int = 50):
    db = get_db_sync()
    try:
        rows = db.execute("SELECT * FROM skill_roadmap_jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return {"items": [dict(r) for r in rows]}
    finally:
        db.close()


# ── Skill relationships compat routes ───────────────────────────

@api_router.get("/skill-relationships/{skill_name}")
def get_skill_relationships_compat(skill_name: str):
    from infrastructure.database.skill_repository import SkillRepository
    db = get_db_sync()
    try:
        return SkillRepository(db).get_relationships(skill_name)
    finally:
        db.close()


@api_router.post("/skill-relationships")
def create_skill_relationship_compat(data: dict):
    from infrastructure.database.skill_repository import SkillRepository
    from exceptions import ConflictError
    db = get_db_sync()
    try:
        success = SkillRepository(db).create_relationship(data)
        if not success:
            raise ConflictError("Relationship already exists")
        return {"status": "created"}
    finally:
        db.close()


@api_router.delete("/skill-relationships/{id}")
def delete_skill_relationship_compat(id: int):
    from infrastructure.database.skill_repository import SkillRepository
    db = get_db_sync()
    try:
        SkillRepository(db).delete_relationship(id)
        return {"status": "deleted"}
    finally:
        db.close()


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
    db = get_db_sync()
    try:
        rows = db.execute("SELECT id FROM pending_companies WHERE status='pending' ORDER BY created_at ASC").fetchall()
        from core.queue import get_queue_manager
        get_queue_manager().enqueue_bulk([dict(r)["id"] for r in rows])
        return {"status": "queued", "count": len(rows)}
    finally:
        db.close()


@api_router.post("/jobs/{num}/link-company")
def link_job_to_company(num: int, data: dict):
    db = get_db_sync()
    try:
        company_id = data.get("company_id")
        if company_id:
            db.execute("UPDATE jobs SET company_id=? WHERE num=?", (company_id, num))
            db.commit()
        return {"status": "linked"}
    finally:
        db.close()


@api_router.post("/companies/{id}/reprocess")
def reprocess_company(id: int):
    db = get_db_sync()
    try:
        company = db.execute("SELECT name FROM companies WHERE id=?", (id,)).fetchone()
        if not company:
            return {"error": "Not found"}
        cur = db.execute(
            "INSERT INTO pending_companies (input_text, input_type, source, status) VALUES (?, ?, ?, ?)",
            (dict(company)["name"], "text", "reprocess", "pending"),
        )
        db.commit()
        from core.queue import get_queue_manager
        get_queue_manager().enqueue(cur.lastrowid, table='pending_companies')
        return {"status": "queued"}
    finally:
        db.close()
