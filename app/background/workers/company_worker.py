"""ARQ worker for company processing.

Delegates to the existing server application services.
Business logic is NOT duplicated here — only execution orchestration.
"""

from background.telemetry.logging import get_logger
from background.infrastructure.database import get_session_sync


log = get_logger("worker.company")


async def process_company(ctx: dict, company_id: int) -> dict:
    log.info("company_worker.start", company_id=company_id)

    try:
        from companies.infrastructure.workers.company_worker import CompanyWorker
        from shared.infrastructure.process.repository import PendingCompanyRepository
        from shared.infrastructure.process_utils import (
            ProcessManager,
            TempFileManager,
            MimoRunner,
            broadcaster,
        )

        session = get_session_sync()
        try:
            pending_repo = PendingCompanyRepository(session)
            proc_mgr = ProcessManager()
            temp_mgr = TempFileManager()
            provider_runner = MimoRunner(proc_mgr)

            worker = CompanyWorker(
                pending_repo=pending_repo,
                process_mgr=proc_mgr,
                temp_mgr=temp_mgr,
                provider_runner=provider_runner,
                broadcaster=broadcaster,
            )
            worker.process(company_id)
        finally:
            session.close()

        log.info("company_worker.complete", company_id=company_id)
        return {"status": "completed", "company_id": company_id}

    except Exception as e:
        log.error("company_worker.failed", company_id=company_id, error=str(e))
        raise
