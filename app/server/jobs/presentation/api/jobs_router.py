"""Job creation and generation routes.

Job listing, detail, and lifecycle endpoints were removed: the V2 jobs list
uses GET /jobs/list (jobs_v2_router) and POST /jobs/{id}/process
(process_router). The retained endpoints below back the AddJobDrawer
(create_job) and the resume feature (generate-resume / generate-cover).
"""

import json
import threading
from fastapi import APIRouter, Depends
from fastapi import status as http_status

from dependencies import get_job_repo, get_session_sync

from jobs.infrastructure import SQLAlchemyJobRepository
from jobs.infrastructure.repositories.sa_tailored_document_repository import SQLAlchemyTailoredDocumentRepository

from shared.application.exceptions import NotFoundError, BadRequestError, JobAlreadyExistsError

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
