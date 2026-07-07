"""Generation endpoints: submit an instruction, poll the job.

POST returns 202 immediately — generation runs on the worker via the Redis
queue, never in the request path.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from forge.jobs import JobQueue

router = APIRouter(prefix="/generate", tags=["generation"])


def get_queue(request: Request) -> JobQueue:
    return JobQueue(request.app.state.redis)


Queue = Depends(get_queue)


class GenerateRequest(BaseModel):
    instruction: str = Field(min_length=5, max_length=4000)
    # Optional explicit workflow name; otherwise the model picks one.
    name: str | None = Field(default=None, max_length=255)
    # Deploy to the engine on success (otherwise the definition is just stored
    # on the job for review).
    deploy: bool = False
    # Approval flag for workflows with destructive nodes (send email, POST...).
    allow_destructive: bool = False
    actor: str = "human"


class JobAccepted(BaseModel):
    job_id: str
    status: str = "queued"


class JobOut(BaseModel):
    job_id: str
    status: str
    payload: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


@router.post("", response_model=JobAccepted, status_code=202)
def submit_generation(body: GenerateRequest, queue: JobQueue = Queue) -> JobAccepted:
    job_id = queue.enqueue(body.model_dump())
    return JobAccepted(job_id=job_id)


@router.get("/{job_id}", response_model=JobOut)
def get_generation_job(job_id: str, queue: JobQueue = Queue) -> JobOut:
    job = queue.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"no job {job_id} (jobs expire after 24h)")
    return JobOut(**job)
