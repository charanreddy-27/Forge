"""Background jobs: Redis-backed queue + worker for workflow generation.

Generation goes through the queue so LLM latency never blocks API requests
(CLAUDE.md scalability requirement). The queue is deliberately minimal —
see ADR-003 for why we didn't pull in a job framework.
"""

from forge.jobs.queue import JobQueue

__all__ = ["JobQueue"]
