"""Pydantic request/response schemas for the workflow registry API."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DeployRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    definition: dict[str, Any]
    comment: str | None = None
    # Recorded in workflow_versions.created_by and the audit trail.
    actor: str = "human"


class RollbackRequest(BaseModel):
    target_version: int = Field(ge=1)
    actor: str = "human"


class WorkflowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    engine_workflow_id: str | None
    status: str
    current_version: int
    created_at: datetime
    updated_at: datetime


class WorkflowVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_id: uuid.UUID
    version: int
    definition: dict[str, Any]
    created_by: str
    comment: str | None
    created_at: datetime
