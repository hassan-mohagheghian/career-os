"""Scheduler for periodic background tasks.

Define cron-based recurring jobs here (e.g. daily cleanup, periodic rescoring).
"""

from arq import cron


async def periodic_job_cleanup(ctx: dict) -> None:
    """Periodic cleanup of stale queued items."""
    from background.telemetry.logging import get_logger
    log = get_logger("scheduler.cleanup")
    log.info("scheduler.cleanup.start")

    try:
        from background.infrastructure.database import get_session_sync
        session = get_session_sync()
        try:
            from jobs.infrastructure import SQLAlchemyJobRepository

            repo = SQLAlchemyJobRepository(session)
            count = repo.cleanup_stale_items(hours=24)
            log.info("scheduler.cleanup.complete", cleaned=count)
        finally:
            session.close()
    except Exception as e:
        log.error("scheduler.cleanup.failed", error=str(e))
