"""Job CRUD, lifecycle, and generation routes."""

import json
import threading
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status

from dependencies import get_job_repo, get_summary_repo, get_tailored_document_repo, get_session_sync

# Bounded context infrastructure
from jobs.infrastructure import SQLAlchemyJobRepository
from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
from jobs.infrastructure.repositories.sa_tailored_document_repository import SQLAlchemyTailoredDocumentRepository

# Application exceptions
from shared.application.exceptions import NotFoundError, BadRequestError, JobAlreadyExistsError

# Pydantic schemas
from jobs.presentation.api.schemas.jobs import CreateJobRequest, CreateJobResponse

router = APIRouter()


@router.post("", status_code=http_status.HTTP_201_CREATED, response_model=CreateJobResponse)
def create_job(
    body: CreateJobRequest,
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
):
    """Create a new job from a job posting URL."""
    existing = repo.get_by_url(body.job_post_url)
    if existing and not existing.get("deleted"):
        raise JobAlreadyExistsError()

    links_json = json.dumps([l.model_dump() for l in body.links], ensure_ascii=False)
    notes_json = json.dumps([n.model_dump() for n in body.notes], ensure_ascii=False)

    job = repo.create_job(
        url=body.job_post_url,
        title=body.job_title,
        notes=notes_json,
        links=links_json,
    )

    return CreateJobResponse(id=job["num"], status=job["status"])


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
    """Get paginated list of all jobs regardless of state."""
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
def get_job_generation_history(num: int, session = Depends(get_session_sync)):
    """Get generation history (resume + cover) for a specific job."""
    repo = SQLAlchemyTailoredDocumentRepository(session)
    items = repo.get_history_for_job(num)
    title_map = {'resume': 'Resume', 'cover': 'Cover Letter', 'cover_letter': 'Cover Letter'}
    return [
        {
            "id": r.get("id", r.get("num", 0)),
            "type": r.get("type", "unknown"),
            "title": title_map.get(r.get("type", ""), r.get("type", "")),
            "status": r["status"],
            "error": r.get("error"),
            "started_at": r.get("created_at"),
            "completed_at": r.get("updated_at") if r.get("status") in ("processed", "failed", "cancelled") else None,
        }
        for r in items
    ]


@router.get("/{num}")
def get_job(
    num: int,
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    doc_repo: SQLAlchemyTailoredDocumentRepository = Depends(get_tailored_document_repo),
):
    """Get a single job by number with its resume and cover letter."""
    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    resume = doc_repo.get_for_job(num)
    cover = doc_repo.get_cover_for_job(num)

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
):
    """Re-queue a job for processing."""
    from shared.infrastructure.taskiq.client import enqueue_job_sync

    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    repo.update_fields(num,
        status='queued', error=None, current_node=None, progress_pct=0,
        retry_count=0, failure_reason=None, failure_step=None,
        failure_timestamp=None, updated_at=datetime.now(UTC).isoformat(),
    )
    enqueue_job_sync(num)
    return {"status": "queued", "num": num}


@router.post("/{num}/rescore")
def rescore_job(
    num: int,
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
):
    """Rescore an existing job. Sets the rescoring flag and re-queues."""
    from shared.infrastructure.taskiq.client import enqueue_job_sync

    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    repo.mark_rescoring(num)
    repo.update_fields(num,
        status='queued', error=None, current_node=None, progress_pct=0,
        retry_count=0, failure_reason=None, failure_step=None,
        failure_timestamp=None, updated_at=datetime.now(UTC).isoformat(),
    )
    enqueue_job_sync(num)
    return {"status": "queued", "num": num}


@router.post("/rescore-all")
def rescore_all(
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
):
    """Rescore all non-deleted jobs."""
    from shared.infrastructure.taskiq.client import enqueue_job_sync

    jobs = repo.get_all_active()
    for job in jobs:
        repo.mark_rescoring(job["num"])
        repo.update_fields(job["num"], status='queued', updated_at=datetime.now(UTC).isoformat())
        enqueue_job_sync(job["num"])
    return {"status": "rescoring", "count": len(jobs)}


@router.post("/reprocess-all")
def reprocess_all(
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
    summary_repo: SQLAlchemySummaryRepository = Depends(get_summary_repo),
):
    """Reprocess all jobs from scratch."""
    from shared.infrastructure.taskiq.client import enqueue_job_sync

    jobs = repo.get_all_active()
    repo.delete_all_active()
    summary_repo.delete_all()

    for job in jobs:
        result = repo.upsert({
            "num": repo.get_next_num(),
            "url": job["url"],
            "company": job.get("company", ""),
            "status": "queued",
        })
        enqueue_job_sync(result["num"])
    return {"status": "reprocessing", "count": len(jobs)}


@router.post("/{num}/cancel")
def cancel_job_lifecycle(num: int, repo: SQLAlchemyJobRepository = Depends(get_job_repo)):
    """Cancel a job's processing."""
    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")
    repo.update_fields(num, status='cancelled', updated_at=datetime.now(UTC).isoformat())
    return {"status": "cancelled", "num": num}


@router.post("/{num}/reset")
def reset_job_lifecycle(num: int, repo: SQLAlchemyJobRepository = Depends(get_job_repo)):
    """Reset a job back to pending."""
    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")
    repo.update_fields(num,
        status='pending', error=None, current_node=None, progress_pct=0,
        retry_count=0, failure_reason=None, failure_step=None,
        failure_timestamp=None, updated_at=datetime.now(UTC).isoformat(),
    )
    return {"status": "reset", "num": num}


@router.get("/status/{status}")
def list_jobs_by_status(
    status: str,
    repo: SQLAlchemyJobRepository = Depends(get_job_repo),
):
    """List jobs by lifecycle status."""
    return repo.list_by_status(status)


@router.post("/{num}/generate-resume")
def generate_resume(num: int, session = Depends(get_session_sync)):
    """Start background resume generation for a job."""
    repo = SQLAlchemyJobRepository(session)
    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    doc_repo = SQLAlchemyTailoredDocumentRepository(session)
    running = doc_repo.get_active_for_job(num, "resume")
    if running:
        raise BadRequestError("A resume generation is already running for this job")

    gen = doc_repo.create_generation(num, "resume")
    gen_id = gen["id"]
    session.commit()

    def _run():
        from jobs.infrastructure.workers.generation_worker import process_generation
        try:
            process_generation(gen_id)
        except Exception as e:
            from shared.infrastructure.process.logging_config import get_logger
            get_logger('jobs').error("Generation failed", gen_id=gen_id, error=str(e))

    threading.Thread(target=_run, daemon=True).start()
    return {"gen_id": gen_id, "status": "queued", "job_num": num}


@router.post("/{num}/generate-cover")
def generate_cover(num: int, session = Depends(get_session_sync)):
    """Start background cover letter generation for a job."""
    repo = SQLAlchemyJobRepository(session)
    job = repo.get_by_num(num)
    if not job:
        raise NotFoundError(f"Job {num} not found")

    doc_repo = SQLAlchemyTailoredDocumentRepository(session)
    running = doc_repo.get_active_for_job(num, "cover")
    if running:
        raise BadRequestError("A cover letter generation is already running for this job")

    gen = doc_repo.create_generation(num, "cover")
    gen_id = gen["id"]
    session.commit()

    def _run():
        from jobs.infrastructure.workers.generation_worker import process_generation
        try:
            process_generation(gen_id)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
    return {"gen_id": gen_id, "status": "queued", "job_num": num}
