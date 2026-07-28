"""Job CRUD, rescore, and reprocess routes."""

import threading
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from dependencies import get_job_repo, get_pending_repo, get_summary_repo, get_resume_repo, get_session_sync

# Bounded context infrastructure
from jobs.infrastructure import SQLAlchemyJobRepository
from processing.infrastructure import SQLAlchemyPendingRepository
from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
from resume.infrastructure import SQLAlchemyResumeRepository

# Application exceptions
from shared.application.exceptions import NotFoundError, BadRequestError

router = APIRouter()


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
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
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
def get_summaries(repo: SQLAlchemySummaryRepository = Depends(get_summary_repo)):
    """Get job summaries sorted by grade."""
    return repo.get_all()


@router.get("/{num}/generation-history")
def get_job_generation_history(num: int, repo: SQLAlchemyPendingRepository = Depends(get_pending_repo)):
    """Get generation history (resume + cover) for a specific job."""
    title_map = {'resume': 'Resume', 'cover': 'Cover Letter', 'cover_letter': 'Cover Letter'}
    items = repo.get_history_for_job(num) if hasattr(repo, 'get_history_for_job') else []
    return [
        {
            "id": r["id"],
            "type": r.get("type", "unknown"),
            "title": title_map.get(r.get("type", ""), r.get("type", "")),
            "status": r["status"],
            "error": r.get("error"),
            "started_at": r.get("created_at"),
            "completed_at": r.get("updated_at") if r.get("status") in ("done", "failed") else None,
        }
        for r in items
    ]


@router.get("/{num}")
def get_job(
    num: int,
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    resume_repo: SQLAlchemyResumeRepository = Depends(get_resume_repo),
):
    """Get a single job by number with its resume and cover letter."""
    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    resume = resume_repo.get_for_job(num)
    cover = resume_repo.get_cover_for_job(num)

    return {
        **job,
        "resume": resume,
        "coverLetter": cover,
    }


@router.put("/{num}")
def update_job(num: int, data: dict, repo: SQLAlchemyJobRepository = Depends(get_job_repo)):
    """Update a job."""
    job = repo.update(num, data)
    if not job:
        raise NotFoundError(f"Job {num} not found")
    return job


@router.delete("/{num}")
def delete_job(num: int, repo: SQLAlchemyJobRepository = Depends(get_job_repo)):
    """Delete a job and related data."""
    repo.delete(num)
    return {"status": "deleted", "num": num}


@router.post("/{num}/requeue")
def requeue_job(
    num: int,
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    pending_repo: SQLAlchemyPendingRepository = Depends(get_pending_repo),
):
    """Re-queue a job for processing."""
    from shared.infrastructure.config.queue import get_queue_manager

    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    url = job["url"]
    company = job.get("company", "")

    repo.mark_deleted(num)
    existing = pending_repo.get_by_url(url)

    if existing:
        pid = existing["id"]
        pending_repo.update_fields(pid, table="pending_jobs",
            status="pending", error=None, source="requeue",
            company=company, queue_order=0, step_fetch=0, step_analyze=0,
            step_extract_raw=0, step_extract_struct=0, step_resume=0, step_cover=0,
            step_db=0, step_done=0, workflow_log="[]",
            updated_at=datetime.now().isoformat())
    else:
        result = pending_repo.create_pending_job(url, "requeue", company, "pending")
        pid = result["id"]

    get_queue_manager().enqueue(pid)
    return {"status": "queued", "pid": pid, "num": num, "company": company}


@router.post("/{num}/rescore")
def rescore_job(
    num: int,
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    pending_repo: SQLAlchemyPendingRepository = Depends(get_pending_repo),
):
    """Rescore an existing job."""
    from shared.infrastructure.config.queue import get_queue_manager

    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    url = job["url"]
    repo.mark_rescoring(num)

    existing = pending_repo.get_by_url(url)
    if existing:
        pending_repo.update_status(str(existing["id"]), "cancelled", table="pending_jobs")

    result = pending_repo.create({
        "url": url,
        "source": "rescore",
        "company": job.get("company", ""),
    })
    pending_id = result["id"]
    get_queue_manager().enqueue(pending_id)
    return {"status": "queued", "num": num, "company": job.get("company", ""), "pending_id": pending_id}


@router.post("/rescore-all")
def rescore_all(
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    pending_repo: SQLAlchemyPendingRepository = Depends(get_pending_repo),
):
    """Rescore all non-deleted jobs."""
    from shared.infrastructure.config.queue import get_queue_manager

    jobs = repo.get_all_active()
    pending_ids = []

    for job in jobs:
        num = job["num"]
        url = job["url"]
        repo.mark_rescoring(num)
        result = pending_repo.create({
            "url": url,
            "source": "rescore",
            "company": job.get("company", ""),
        })
        pending_ids.append(result["id"])

    if pending_ids:
        get_queue_manager().enqueue_bulk(pending_ids)
    return {"status": "rescoring", "count": len(pending_ids)}


@router.post("/reprocess-all")
def reprocess_all(
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    pending_repo: SQLAlchemyPendingRepository = Depends(get_pending_repo),
    summary_repo: SQLAlchemySummaryRepository = Depends(get_summary_repo),
):
    """Reprocess all jobs from scratch."""
    from shared.infrastructure.config.queue import get_queue_manager

    jobs = repo.get_all_active()
    repo.delete_all_active()
    summary_repo.delete_all()

    pending_ids = []
    for job in jobs:
        url = job["url"]
        company = job.get("company", "")
        existing = pending_repo.get_by_url(url)

        if existing:
            pid = existing["id"]
            pending_repo.update_fields(pid, table="pending_jobs",
                status="pending", error=None, source="requeue",
                company=company, queue_order=0, step_fetch=0, step_analyze=0,
                step_extract_raw=0, step_extract_struct=0, step_resume=0, step_cover=0,
                step_db=0, step_done=0, workflow_log="[]",
                updated_at=datetime.now().isoformat())
            pending_ids.append(pid)
        else:
            result = pending_repo.create(url, {
                "url": url,
                "source": "requeue",
                "company": company,
            })
            pending_ids.append(result["id"])

    if pending_ids:
        get_queue_manager().enqueue_bulk(pending_ids)
    return {"status": "reprocessing", "count": len(pending_ids)}


@router.post("/{num}/generate-resume")
def generate_resume(num: int, pending_repo: SQLAlchemyPendingRepository = Depends(get_pending_repo), session = Depends(get_session_sync)):
    """Start background resume generation for a job."""
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository

    repo = SQLAlchemyJobRepository(session)
    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    from processing.infrastructure.repositories.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
    gen_repo = SQLAlchemyPendingGenerationRepository(session)

    running = gen_repo.get_active_for_job(num, "resume")
    if running:
        raise BadRequestError("A resume generation is already running for this job")

    gen = gen_repo.create(num, "resume", "queued")
    gen_id = gen["id"]
    session.commit()

    def _run():
        from resume.infrastructure.workers.generation_worker import process_generation
        try:
            process_generation(gen_id)
        except Exception as e:
            import logging
            logging.getLogger('jobs').error(f"Generation {gen_id} failed: {e}")
            try:
                s = get_session_sync()
                try:
                    from processing.infrastructure.repositories.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
                    SQLAlchemyPendingGenerationRepository(s).update_fields(gen_id, status="failed", error=str(e))
                    s.commit()
                finally:
                    pass
            except Exception:
                pass

    threading.Thread(target=_run, daemon=True).start()
    return {"gen_id": gen_id, "status": "queued", "job_num": num}


@router.post("/{num}/generate-cover")
def generate_cover(num: int, session = Depends(get_session_sync)):
    """Start background cover letter generation for a job."""
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    from processing.infrastructure.repositories.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository

    repo = SQLAlchemyJobRepository(session)
    job = repo.get_by_num(num)
    if not job:
        from shared.application.exceptions import NotFoundError
        raise NotFoundError(f"Job {num} not found")

    gen_repo = SQLAlchemyPendingGenerationRepository(session)
    running = gen_repo.get_active_for_job(num, "cover")
    if running:
        from shared.application.exceptions import BadRequestError
        raise BadRequestError("A cover letter generation is already running for this job")

    gen = gen_repo.create(num, "cover", "queued")
    gen_id = gen["id"]
    session.commit()

    def _run():
        from resume.infrastructure.workers.generation_worker import process_generation
        try:
            process_generation(gen_id)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
    return {"gen_id": gen_id, "status": "queued", "job_num": num}
