"""Minimal Redis job queue.

- Jobs wait on a Redis list (LPUSH / BRPOP → FIFO).
- Job state lives in a hash per job: status, payload, result, error, timestamps.
- Statuses: queued → running → succeeded | failed | requires_approval.

State is JSON-in-Redis rather than Postgres because jobs are transient
plumbing; anything durable (the workflow, its versions, the audit trail)
lands in Postgres via the registry when the job succeeds.
"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any, Protocol

QUEUE_KEY = "forge:generation:queue"
# Finished jobs linger for a day so clients can poll results, then expire.
JOB_TTL_SECONDS = 24 * 3600


class RedisLike(Protocol):
    """The slice of redis.Redis the queue uses (decode_responses=True).

    Returns are Any because redis-py's stubs type them as wide str|bytes
    unions; with decode_responses=True everything is str at runtime.
    """

    def lpush(self, name: str, *values: str) -> Any: ...
    def brpop(self, keys: str, timeout: int) -> Any: ...
    def hset(self, name: str, *, mapping: dict[str, str]) -> Any: ...
    def hgetall(self, name: str) -> Any: ...
    def expire(self, name: str, time: int) -> Any: ...


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _job_key(job_id: str) -> str:
    return f"forge:jobs:{job_id}"


class JobQueue:
    def __init__(self, redis_client: RedisLike) -> None:
        self._redis = redis_client

    def enqueue(self, payload: dict[str, Any]) -> str:
        job_id = uuid.uuid4().hex
        self._redis.hset(
            _job_key(job_id),
            mapping={
                "status": "queued",
                "payload": json.dumps(payload),
                "created_at": _now(),
            },
        )
        self._redis.expire(_job_key(job_id), JOB_TTL_SECONDS)
        self._redis.lpush(QUEUE_KEY, job_id)
        return job_id

    def claim(self, timeout: int = 5) -> tuple[str, dict[str, Any]] | None:
        """Block up to `timeout` seconds for the next job; mark it running."""
        item = self._redis.brpop(QUEUE_KEY, timeout=timeout)
        if item is None:
            return None
        job_id = item[1]
        record = self._redis.hgetall(_job_key(job_id))
        payload: dict[str, Any] = json.loads(record.get("payload", "{}"))
        self._update(job_id, status="running", started_at=_now())
        return job_id, payload

    def finish(self, job_id: str, status: str, result: dict[str, Any]) -> None:
        self._update(
            job_id, status=status, result=json.dumps(result), finished_at=_now()
        )

    def fail(self, job_id: str, error: str) -> None:
        self._update(job_id, status="failed", error=error, finished_at=_now())

    def get(self, job_id: str) -> dict[str, Any] | None:
        record = self._redis.hgetall(_job_key(job_id))
        if not record:
            return None
        parsed: dict[str, Any] = dict(record)
        for json_field in ("payload", "result"):
            if json_field in parsed:
                parsed[json_field] = json.loads(parsed[json_field])
        parsed["job_id"] = job_id
        return parsed

    def _update(self, job_id: str, **fields: str) -> None:
        self._redis.hset(_job_key(job_id), mapping=fields)
        self._redis.expire(_job_key(job_id), JOB_TTL_SECONDS)
