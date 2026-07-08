"""ORM models for the Forge data layer.

Tables:
- workflows / workflow_versions — the versioned workflow registry
- runs                          — execution history ingested from the engine
- incidents                     — failures awaiting diagnosis or approval
- llm_calls                     — cost/latency log for every LLM call
- audit_log                     — every agent action, destructive or not

JSON columns use JSONB on Postgres but degrade to plain JSON elsewhere so the
test suite can run against SQLite.
"""

import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from forge.db.base import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(UTC)


class WorkflowStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class RunStatus(enum.StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"


class IncidentStatus(enum.StrEnum):
    OPEN = "open"
    AWAITING_APPROVAL = "awaiting_approval"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # ID assigned by the workflow engine (n8n) once deployed. Kept generic so
    # the engine stays swappable behind the engine_adapter.
    engine_workflow_id: Mapped[str | None] = mapped_column(String(255), index=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus, native_enum=False, length=32), default=WorkflowStatus.DRAFT
    )
    # Points at the workflow_versions.version currently deployed; 0 = never deployed.
    current_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    versions: Mapped[list["WorkflowVersion"]] = relationship(back_populates="workflow")
    runs: Mapped[list["Run"]] = relationship(back_populates="workflow")


class WorkflowVersion(Base):
    """Immutable snapshot of a workflow definition. Rollback = redeploy an old row."""

    __tablename__ = "workflow_versions"
    __table_args__ = (
        UniqueConstraint("workflow_id", "version", name="uq_workflow_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflows.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    definition: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    # Who produced this version: "human" or an agent service name.
    created_by: Mapped[str] = mapped_column(String(64), nullable=False, default="human")
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    workflow: Mapped[Workflow] = relationship(back_populates="versions")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflows.id"), nullable=False, index=True
    )
    engine_execution_id: Mapped[str | None] = mapped_column(String(255), index=True)
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, native_enum=False, length=32), default=RunStatus.RUNNING
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    # Raw execution data from the engine, for the diagnostician.
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONType)

    workflow: Mapped[Workflow] = relationship(back_populates="runs")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflows.id"), nullable=False, index=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("runs.id"))
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, native_enum=False, length=32), default=IncidentStatus.OPEN
    )
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[str | None] = mapped_column(Text)
    # Patch proposed by the diagnostician; applied only after approval when risky.
    proposed_patch: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LLMCall(Base):
    """One row per LLM call, successful or not. The budget guard sums cost_usd."""

    __tablename__ = "llm_calls"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    # Which agent service made the call (workflow-generator, diagnostician, ...).
    service: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Free-text purpose for the cost dashboard ("generate workflow", ...).
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    # Numeric(12, 6): six decimal places keeps sub-cent costs exact.
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("0"))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(default=True)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class AuditLog(Base):
    """Append-only trail of every agent action. Never updated, never deleted."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # "human:<name>" or an agent service name.
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
