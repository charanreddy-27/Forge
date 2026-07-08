"""Generation worker: claims queued jobs and runs them.

Run with:  python -m forge.jobs.worker
The compose service `generation-worker` does exactly that, sharing the
agent-layer image. Scale by running more workers — BRPOP hands each job to
exactly one of them.
"""

import logging
from collections.abc import Callable
from typing import Any, cast

import redis

from forge.config import get_settings
from forge.db.base import create_db_engine, create_session_factory
from forge.engine_adapter import N8nAdapter
from forge.generator import WorkflowGenerator
from forge.jobs.handlers import GenerationJobHandler
from forge.jobs.queue import JobQueue, RedisLike
from forge.llm_gateway import LLMGateway
from forge.logsetup import configure_logging
from forge.registry import WorkflowRegistry

logger = logging.getLogger(__name__)

Handler = Callable[[dict[str, Any]], tuple[str, dict[str, Any]]]


def run_worker(queue: JobQueue, handler: Handler, *, run_forever: bool = True) -> None:
    """Claim-execute loop. run_forever=False processes at most one claim (tests)."""
    while True:
        claimed = queue.claim(timeout=5)
        if claimed is not None:
            job_id, payload = claimed
            logger.info(
                "job %s claimed: %s", job_id, payload.get("instruction", "")[:80]
            )
            try:
                status, result = handler(payload)
                queue.finish(job_id, status, result)
                logger.info("job %s finished: %s", job_id, status)
            except Exception as exc:  # any crash must land in the job record
                logger.exception("job %s crashed", job_id)
                queue.fail(job_id, f"{type(exc).__name__}: {exc}")
        if not run_forever:
            return


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_format)

    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    # cast: redis-py's stubs return str|bytes unions, but decode_responses=True
    # guarantees str at runtime — RedisLike documents the shape we rely on.
    redis_client = cast(
        RedisLike, redis.Redis.from_url(settings.redis_url, decode_responses=True)
    )
    queue = JobQueue(redis_client)
    handler = GenerationJobHandler(
        generator=WorkflowGenerator(LLMGateway(session_factory, settings)),
        registry=WorkflowRegistry(
            session_factory, N8nAdapter(settings.n8n_base_url, settings.n8n_api_key)
        ),
    )

    logger.info("generation worker started (queue: forge:generation:queue)")
    run_worker(queue, handler)


if __name__ == "__main__":
    main()
