"""Incident endpoints: the human side of the diagnostician loop."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from forge.db.models import Incident
from forge.diagnostician import (
    Diagnostician,
    IncidentNotFoundError,
    IncidentStateError,
)
from forge.llm_gateway import LLMGateway
from forge.registry import WorkflowRegistry

router = APIRouter(prefix="/incidents", tags=["incidents"])


def get_diagnostician(request: Request) -> Diagnostician:
    settings = request.app.state.settings
    session_factory = request.app.state.session_factory
    registry = WorkflowRegistry(
        session_factory=session_factory, adapter=request.app.state.engine_adapter
    )
    return Diagnostician(
        session_factory=session_factory,
        gateway=LLMGateway(session_factory, settings),
        registry=registry,
        auto_apply=settings.diagnostician_auto_apply,
    )


Diag = Depends(get_diagnostician)


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_id: uuid.UUID
    run_id: uuid.UUID | None
    status: str
    severity: str
    summary: str
    root_cause: str | None
    proposed_patch: dict[str, Any] | None
    created_at: datetime
    resolved_at: datetime | None


class ApproveRequest(BaseModel):
    actor: str = "human"


@router.get("", response_model=list[IncidentOut])
def list_incidents(request: Request, status: str | None = None) -> list[IncidentOut]:
    query = select(Incident).order_by(Incident.created_at.desc())
    if status is not None:
        query = query.where(Incident.status == status)
    with request.app.state.session_factory() as session:
        incidents = session.execute(query).scalars().all()
    return [IncidentOut.model_validate(i) for i in incidents]


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: uuid.UUID, request: Request) -> IncidentOut:
    with request.app.state.session_factory() as session:
        incident = session.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"no incident {incident_id}")
    return IncidentOut.model_validate(incident)


@router.post("/{incident_id}/approve", response_model=IncidentOut)
def approve_incident(
    incident_id: uuid.UUID, body: ApproveRequest, diagnostician: Diagnostician = Diag
) -> IncidentOut:
    """Apply the awaiting patch: deploys it as a new version (audited), resolves."""
    try:
        incident = diagnostician.approve(incident_id, actor=body.actor)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IncidentStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return IncidentOut.model_validate(incident)


@router.post("/{incident_id}/dismiss", response_model=IncidentOut)
def dismiss_incident(incident_id: uuid.UUID, diagnostician: Diagnostician = Diag) -> IncidentOut:
    try:
        incident = diagnostician.dismiss(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return IncidentOut.model_validate(incident)
