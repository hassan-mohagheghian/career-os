"""Job CRUD, rescore, and reprocess routes."""

import json
import threading
from datetime import datetime

from fastapi import APIRouter, Depends, Query
import sqlite3

from dependencies import get_db
from infrastructure.database.job_repository import JobRepository
from exceptions import NotFoundError, BadRequestError

router = APIRouter()


def _get_repo(db: sqlite3.Connection = Depends(get_db)) -> JobRepository:
    return JobRepository(db)


@router.get("")
def list_jobs(
    offset: int | None = Query(None, ge=0),
    limit: int | None = Query(None, ge=1, le=200),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    filter_tech: str = Query(""),
    filter_cities: str = Query(""),
    filter_companies: str = Query(""),
    filter_matches: str = Query(""),
    filter_work_types: str = Query(""),
    filter_employment_types: str = Query(""),
    filter_response_status: str = Query(""),
    filter_applied: str = Query(""),
    filter_scores: str = Query(""),
    repo: JobRepository = Depends(_get_repo),
):
    """Get paginated list of processed jobs."""
    filters = {
        "filter_tech": filter_tech,
        "filter_cities": filter_cities,
        "filter_companies": filter_companies,
        "filter_matches": filter_matches,
        "filter_work_types": filter_work_types,
        "filter_employment_types": filter_employment_types,
        "filter_response_status": filter_response_status,
        "filter_applied": filter_applied,
        "filter_scores": filter_scores,
    }
    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v}

    jobs, total = repo.list_jobs(
        offset=offset,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        filters=filters if filters else None,
    )
    agg = repo.get_stats()
    return {"jobs": jobs, "total": total, "agg": agg}


@router.get("/summaries")
def get_summaries(db: sqlite3.Connection = Depends(get_db)):
    """Get job summaries sorted by grade."""
    grade_order = "CASE score WHEN 'A++' THEN 7 WHEN 'A+' THEN 6 WHEN 'A' THEN 5 WHEN 'B' THEN 4 WHEN 'C' THEN 3 WHEN 'D' THEN 2 WHEN 'E' THEN 1 ELSE 0 END"
    rows = db.execute(f"SELECT * FROM summaries ORDER BY {grade_order} DESC").fetchall()
    return [dict(r) for r in rows]


@router.get("/{num}/generation-history")
def get_job_generation_history(num: int, db: sqlite3.Connection = Depends(get_db)):
    """Get generation history (resume + cover) for a specific job."""
    rows = db.execute(
        "SELECT id, type, status, error, created_at, updated_at "
        "FROM pending_generations WHERE job_num=? ORDER BY created_at DESC",
        (num,),
    ).fetchall()
    title_map = {'resume': 'Resume', 'cover': 'Cover Letter', 'cover_letter': 'Cover Letter'}
    return [
        {
            "id": r["id"],
            "type": r["type"],
            "title": title_map.get(r["type"], r["type"]),
            "status": r["status"],
            "error": r["error"],
            "started_at": r["created_at"],
            "completed_at": r["updated_at"] if r["status"] in ("done", "failed") else None,
        }
        for r in rows
    ]


@router.get("/{num}")
def get_job(num: int, repo: JobRepository = Depends(_get_repo), db: sqlite3.Connection = Depends(get_db)):
    """Get a single job by number with its resume and cover letter."""
    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    resume = db.execute(
        "SELECT id, title, content, job_num FROM resumes WHERE job_num=? AND id NOT LIKE 'cover_%' ORDER BY created_at DESC LIMIT 1",
        (num,),
    ).fetchone()
    cover = db.execute(
        "SELECT id, title, content, job_num FROM resumes WHERE job_num=? AND id LIKE 'cover_%' ORDER BY created_at DESC LIMIT 1",
        (num,),
    ).fetchone()

    return {
        **job,
        "resume": dict(resume) if resume else None,
        "coverLetter": dict(cover) if cover else None,
    }


@router.put("/{num}")
def update_job(num: int, data: dict, repo: JobRepository = Depends(_get_repo)):
    """Update a job."""
    job = repo.update(num, data)
    if not job:
        raise NotFoundError(f"Job {num} not found")
    return job


@router.delete("/{num}")
def delete_job(num: int, repo: JobRepository = Depends(_get_repo)):
    """Delete a job and related data."""
    repo.delete(num)
    return {"status": "deleted", "num": num}


@router.post("/{num}/requeue")
def requeue_job(num: int, repo: JobRepository = Depends(_get_repo), db: sqlite3.Connection = Depends(get_db)):
    """Re-queue a job for processing."""
    from core.queue import get_queue_manager

    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    url = job["url"]
    company = job.get("company", "")

    repo.mark_deleted(num)
    row = db.execute("SELECT id FROM pending_jobs WHERE url=?", (url,)).fetchone()

    if row:
        pid = dict(row)["id"]
        db.execute(
            """UPDATE pending_jobs SET status='pending', error=NULL, source='requeue',
            company=?, queue_order=0, step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
            step_analyze=0, step_summary=0, step_db=0, step_done=0,
            workflow_log='[]', updated_at=? WHERE id=?""",
            (company, datetime.now().isoformat(), pid),
        )
    else:
        cur = db.execute(
            "INSERT INTO pending_jobs (url, source, company, status) VALUES (?, ?, ?, ?)",
            (url, "requeue", company, "pending"),
        )
        pid = cur.lastrowid

    db.commit()
    get_queue_manager().enqueue(pid)
    return {"status": "queued", "pid": pid, "num": num, "company": company}


@router.post("/{num}/rescore")
def rescore_job(num: int, repo: JobRepository = Depends(_get_repo), db: sqlite3.Connection = Depends(get_db)):
    """Rescore an existing job."""
    from core.queue import get_queue_manager

    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    url = job["url"]
    repo.mark_rescoring(num)
    db.execute("DELETE FROM pending_jobs WHERE url=?", (url,))
    cur = db.execute(
        "INSERT INTO pending_jobs (url, source, company, job_num, status) VALUES (?, ?, ?, ?, ?)",
        (url, "rescore", job.get("company", ""), num, "pending"),
    )
    db.commit()
    pending_id = cur.lastrowid
    get_queue_manager().enqueue(pending_id)
    return {"status": "queued", "num": num, "company": job.get("company", ""), "pending_id": pending_id}


@router.post("/rescore-all")
def rescore_all(repo: JobRepository = Depends(_get_repo), db: sqlite3.Connection = Depends(get_db)):
    """Rescore all non-deleted jobs."""
    from core.queue import get_queue_manager

    jobs = repo.get_all_active()
    count = 0
    pending_ids = []

    for job in jobs:
        num = job["num"]
        url = job["url"]
        repo.mark_rescoring(num)
        cur = db.execute(
            "INSERT INTO pending_jobs (url, source, company, job_num, status) VALUES (?, ?, ?, ?, ?)",
            (url, "rescore", job.get("company", ""), num, "pending"),
        )
        pending_ids.append(cur.lastrowid)
        count += 1

    db.commit()
    if pending_ids:
        get_queue_manager().enqueue_bulk(pending_ids)
    return {"status": "rescoring", "count": count}


@router.post("/reprocess-all")
def reprocess_all(repo: JobRepository = Depends(_get_repo), db: sqlite3.Connection = Depends(get_db)):
    """Reprocess all jobs from scratch."""
    from core.queue import get_queue_manager

    jobs = repo.get_all_active()
    db.execute("DELETE FROM jobs WHERE deleted=0")
    db.execute("DELETE FROM summaries")
    db.execute("DELETE FROM resumes WHERE id != 'original'")

    pending_ids = []
    for job in jobs:
        url = job["url"]
        company = job.get("company", "")
        row = db.execute("SELECT id FROM pending_jobs WHERE url=?", (url,)).fetchone()

        if row:
            pid = dict(row)["id"]
            db.execute(
                """UPDATE pending_jobs SET status='pending', error=NULL, source='requeue',
                company=?, queue_order=0, step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
                step_analyze=0, step_summary=0, step_db=0, step_done=0,
                workflow_log='[]', updated_at=? WHERE id=?""",
                (company, datetime.now().isoformat(), pid),
            )
            pending_ids.append(pid)
        else:
            cur = db.execute(
                "INSERT INTO pending_jobs (url, source, company, status) VALUES (?, ?, ?, ?)",
                (url, "requeue", company, "pending"),
            )
            pending_ids.append(cur.lastrowid)

    db.commit()
    if pending_ids:
        get_queue_manager().enqueue_bulk(pending_ids)
    return {"status": "reprocessing", "count": len(pending_ids)}


@router.post("/{num}/generate-resume")
def generate_resume(num: int, db: sqlite3.Connection = Depends(get_db)):
    """Start background resume generation for a job."""
    job = db.execute("SELECT num, company, role FROM jobs WHERE num=? AND deleted=0", (num,)).fetchone()
    if not job:
        raise NotFoundError(f"Job {num} not found")

    running = db.execute(
        "SELECT id FROM pending_generations WHERE job_num=? AND type='resume' AND status IN ('queued','processing')",
        (num,),
    ).fetchone()
    if running:
        raise BadRequestError("A resume generation is already running for this job")

    cur = db.execute(
        "INSERT INTO pending_generations (job_num, type, status) VALUES (?, ?, ?)",
        (num, 'resume', 'queued'),
    )
    db.commit()
    gen_id = cur.lastrowid

    def _run():
        from services.generation_worker import process_generation
        try:
            process_generation(gen_id)
        except Exception as e:
            import logging
            logging.getLogger('jobs').error(f"Generation {gen_id} failed: {e}")
            try:
                db2 = get_db()
                db2.execute("UPDATE pending_generations SET status='failed', error=? WHERE id=?", (str(e), gen_id))
                db2.commit()
                db2.close()
            except Exception:
                pass

    threading.Thread(target=_run, daemon=True).start()
    return {"gen_id": gen_id, "status": "queued", "job_num": num}


@router.post("/{num}/generate-cover")
def generate_cover(num: int, db: sqlite3.Connection = Depends(get_db)):
    """Start background cover letter generation for a job."""
    job = db.execute("SELECT num, company, role FROM jobs WHERE num=? AND deleted=0", (num,)).fetchone()
    if not job:
        raise NotFoundError(f"Job {num} not found")

    running = db.execute(
        "SELECT id FROM pending_generations WHERE job_num=? AND type='cover' AND status IN ('queued','processing')",
        (num,),
    ).fetchone()
    if running:
        raise BadRequestError("A cover letter generation is already running for this job")

    cur = db.execute(
        "INSERT INTO pending_generations (job_num, type, status) VALUES (?, ?, ?)",
        (num, 'cover', 'queued'),
    )
    db.commit()
    gen_id = cur.lastrowid

    def _run():
        from services.generation_worker import process_generation
        try:
            process_generation(gen_id)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
    return {"gen_id": gen_id, "status": "queued", "job_num": num}
