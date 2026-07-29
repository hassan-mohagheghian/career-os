"""ARQ worker for resume/cover letter generation.

Delegates to the existing server application services.
Business logic is NOT duplicated here — only execution orchestration.
"""

from background.telemetry.logging import get_logger


log = get_logger("worker.generation")


async def process_generation(ctx: dict, gen_id: int) -> dict:
    log.info("generation_worker.start", gen_id=gen_id)

    try:
        from jobs.infrastructure.workers.generation_worker import process_generation as server_process_generation

        server_process_generation(gen_id)

        log.info("generation_worker.complete", gen_id=gen_id)
        return {"status": "completed", "gen_id": gen_id}

    except Exception as e:
        log.error("generation_worker.failed", gen_id=gen_id, error=str(e))
        raise
