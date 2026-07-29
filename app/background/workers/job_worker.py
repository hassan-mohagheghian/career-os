"""ARQ worker for job processing.

Delegates to the existing server application services.
Business logic is NOT duplicated here — only execution orchestration.
"""

from background.telemetry.logging import get_logger
from background.infrastructure.database import get_session_sync


log = get_logger("worker.job")


async def process_job(ctx: dict, job_id: int) -> dict:
    log.info("job_worker.start", job_id=job_id)

    try:
        from jobs.infrastructure.workers.job_worker import JobWorker
        from shared.infrastructure.process.repository import PendingJobRepository
        from shared.infrastructure.process_utils import (
            ProcessManager,
            TempFileManager,
            MimoRunner,
            broadcaster,
        )

        session = get_session_sync()
        try:
            pending_repo = PendingJobRepository(session)
            proc_mgr = ProcessManager()
            temp_mgr = TempFileManager()
            provider_runner = MimoRunner(proc_mgr)

            worker = JobWorker(
                pending_repo=pending_repo,
                process_mgr=proc_mgr,
                temp_mgr=temp_mgr,
                provider_runner=provider_runner,
                broadcaster=broadcaster,
            )
            worker.process(job_id)
        finally:
            session.close()

        log.info("job_worker.complete", job_id=job_id)
        return {"status": "completed", "job_id": job_id}

    except Exception as e:
        log.error("job_worker.failed", job_id=job_id, error=str(e))
        raise
