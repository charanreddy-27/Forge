"""Workflow registry endpoints.

Thin HTTP layer over :class:`forge.registry.WorkflowRegistry`; all rules
(versioning, backups, audit) live in the registry, not here.
"""

import uuid
from collections.abc import Callable
from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, Request

from forge.api.schemas import DeployRequest, RollbackRequest, WorkflowOut, WorkflowVersionOut
from forge.engine_adapter import EngineError, EngineNotFoundError
from forge.registry import VersionNotFoundError, WorkflowNotFoundError, WorkflowRegistry

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_registry(request: Request) -> WorkflowRegistry:
    return WorkflowRegistry(
        session_factory=request.app.state.session_factory,
        adapter=request.app.state.engine_adapter,
    )


Registry = Depends(get_registry)


@router.get("", response_model=list[WorkflowOut])
def list_workflows(registry: WorkflowRegistry = Registry) -> list[WorkflowOut]:
    return [WorkflowOut.model_validate(w) for w in registry.list_workflows()]


@router.post("", response_model=WorkflowOut, status_code=201)
def deploy_workflow(body: DeployRequest, registry: WorkflowRegistry = Registry) -> WorkflowOut:
    """Create a workflow and deploy version 1 to the engine."""
    workflow = _translate(
        lambda: registry.deploy(
            name=body.name, definition=body.definition, actor=body.actor, comment=body.comment
        )
    )
    return WorkflowOut.model_validate(workflow)


@router.get("/{workflow_id}", response_model=WorkflowOut)
def get_workflow(workflow_id: uuid.UUID, registry: WorkflowRegistry = Registry) -> WorkflowOut:
    return WorkflowOut.model_validate(_translate(lambda: registry.get_workflow(workflow_id)))


@router.put("/{workflow_id}", response_model=WorkflowOut)
def redeploy_workflow(
    workflow_id: uuid.UUID, body: DeployRequest, registry: WorkflowRegistry = Registry
) -> WorkflowOut:
    """Deploy a new version of an existing workflow."""
    workflow = _translate(
        lambda: registry.deploy(
            name=body.name,
            definition=body.definition,
            workflow_id=workflow_id,
            actor=body.actor,
            comment=body.comment,
        )
    )
    return WorkflowOut.model_validate(workflow)


@router.get("/{workflow_id}/versions", response_model=list[WorkflowVersionOut])
def list_versions(
    workflow_id: uuid.UUID, registry: WorkflowRegistry = Registry
) -> list[WorkflowVersionOut]:
    versions = _translate(lambda: registry.list_versions(workflow_id))
    return [WorkflowVersionOut.model_validate(v) for v in versions]


@router.post("/{workflow_id}/rollback", response_model=WorkflowOut)
def rollback_workflow(
    workflow_id: uuid.UUID, body: RollbackRequest, registry: WorkflowRegistry = Registry
) -> WorkflowOut:
    """One-call rollback to any previous version."""
    workflow = _translate(
        lambda: registry.rollback(workflow_id, body.target_version, actor=body.actor)
    )
    return WorkflowOut.model_validate(workflow)


@router.post("/{workflow_id}/activate", response_model=WorkflowOut)
def activate_workflow(workflow_id: uuid.UUID, registry: WorkflowRegistry = Registry) -> WorkflowOut:
    return WorkflowOut.model_validate(_translate(lambda: registry.set_active(workflow_id, True)))


@router.post("/{workflow_id}/deactivate", response_model=WorkflowOut)
def deactivate_workflow(
    workflow_id: uuid.UUID, registry: WorkflowRegistry = Registry
) -> WorkflowOut:
    return WorkflowOut.model_validate(_translate(lambda: registry.set_active(workflow_id, False)))


@router.delete("/{workflow_id}", status_code=204)
def delete_workflow(workflow_id: uuid.UUID, registry: WorkflowRegistry = Registry) -> None:
    """Delete from the engine (after a pre-delete backup version); history is kept."""
    _translate(lambda: registry.delete(workflow_id))


T = TypeVar("T")


def _translate(action: Callable[[], T]) -> T:
    """Map domain errors onto HTTP codes in one place."""
    try:
        return action()
    except (WorkflowNotFoundError, VersionNotFoundError, EngineNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EngineError as exc:
        raise HTTPException(status_code=502, detail=f"engine error: {exc}") from exc
