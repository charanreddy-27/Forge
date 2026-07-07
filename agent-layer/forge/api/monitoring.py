"""Run history + health endpoints, and a manual sync trigger."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from forge.db.models import Run, Workflow
from forge.monitor import RunMonitor

router = APIRouter(tags=["monitoring"])


def get_monitor(request: Request) -> RunMonitor:
    return RunMonitor(
        session_factory=request.app.state.session_factory,
        adapter=request.app.state.engine_adapter,
    )


Monitor = Depends(get_monitor)


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_id: uuid.UUID
    engine_execution_id: str | None
    status: str
    started_at: datetime
    finished_at: datetime | None
    error_message: str | None


@router.get("/workflows/{workflow_id}/runs", response_model=list[RunOut])
def list_runs(workflow_id: uuid.UUID, request: Request, limit: int = 50) -> list[RunOut]:
    with request.app.state.session_factory() as session:
        if session.get(Workflow, workflow_id) is None:
            raise HTTPException(status_code=404, detail=f"no workflow {workflow_id}")
        runs = (
            session.execute(
                select(Run)
                .where(Run.workflow_id == workflow_id)
                .order_by(Run.started_at.desc())
                .limit(min(limit, 200))
            )
            .scalars()
            .all()
        )
    return [RunOut.model_validate(run) for run in runs]


@router.get("/workflows/{workflow_id}/health")
def workflow_health(
    workflow_id: uuid.UUID, request: Request, monitor: RunMonitor = Monitor
) -> dict[str, Any]:
    with request.app.state.session_factory() as session:
        if session.get(Workflow, workflow_id) is None:
            raise HTTPException(status_code=404, detail=f"no workflow {workflow_id}")
    return monitor.health(workflow_id).as_dict()


@router.post("/monitor/sync")
def sync_now(monitor: RunMonitor = Monitor) -> dict[str, Any]:
    """Pull executions from the engine immediately (the worker also polls).

    Newly failed runs are reported but NOT diagnosed here — diagnosis is an
    LLM call and belongs on the worker, not in a request handler.
    """
    failed = monitor.sync_all()
    return {"newly_failed_runs": [str(run.id) for run in failed]}
