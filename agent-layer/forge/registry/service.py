"""The workflow registry: every deploy is an immutable version in Postgres.

Rules enforced here (from CLAUDE.md):
- every deploy stores a versioned copy BEFORE touching the engine;
- rollback to any previous version is one call;
- destructive actions (delete, overwrite) always snapshot first and write
  to the audit trail — nothing is ever silently destructive.
"""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from forge.db.models import AuditLog, Workflow, WorkflowStatus, WorkflowVersion
from forge.engine_adapter import EngineAdapter


class WorkflowNotFoundError(Exception):
    """No workflow with that ID in the registry."""


class VersionNotFoundError(Exception):
    """The workflow exists but has no such version."""


class WorkflowRegistry:
    """Versioned workflow store + engine deployment, in one place."""

    def __init__(self, session_factory: sessionmaker, adapter: EngineAdapter) -> None:
        self._session_factory = session_factory
        self._adapter = adapter

    # ── reads ────────────────────────────────────────────────────────────

    def list_workflows(self) -> list[Workflow]:
        with self._session_factory() as session:
            rows = (
                session.execute(select(Workflow).order_by(Workflow.created_at))
                .scalars()
                .all()
            )
            return list(rows)

    def get_workflow(self, workflow_id: uuid.UUID) -> Workflow:
        with self._session_factory() as session:
            return self._get(session, workflow_id)

    def list_versions(self, workflow_id: uuid.UUID) -> list[WorkflowVersion]:
        with self._session_factory() as session:
            self._get(session, workflow_id)  # 404 before returning an empty list
            rows = (
                session.execute(
                    select(WorkflowVersion)
                    .where(WorkflowVersion.workflow_id == workflow_id)
                    .order_by(WorkflowVersion.version.desc())
                )
                .scalars()
                .all()
            )
            return list(rows)

    # ── writes ───────────────────────────────────────────────────────────

    def deploy(
        self,
        *,
        name: str,
        definition: dict[str, Any],
        workflow_id: uuid.UUID | None = None,
        actor: str = "human",
        comment: str | None = None,
    ) -> Workflow:
        """Deploy a definition: new workflow when workflow_id is None, else a new version.

        The version row is written in the same transaction that records the
        engine result — if the engine call fails, nothing is committed.
        """
        with self._session_factory() as session:
            if workflow_id is None:
                workflow = Workflow(name=name, status=WorkflowStatus.DRAFT)
                session.add(workflow)
                session.flush()  # assign workflow.id for the version row
            else:
                workflow = self._get(session, workflow_id)
                workflow.name = name

            version = self._add_version(session, workflow, definition, actor, comment)

            if workflow.engine_workflow_id is None:
                engine_wf = self._adapter.create_workflow(definition)
                workflow.engine_workflow_id = engine_wf.id
            else:
                self._adapter.update_workflow(workflow.engine_workflow_id, definition)

            workflow.current_version = version.version
            if workflow.status == WorkflowStatus.DRAFT:
                workflow.status = (
                    WorkflowStatus.INACTIVE
                )  # deployed but not yet activated

            self._audit(
                session,
                actor=actor,
                action="workflow.deploy",
                workflow=workflow,
                detail={"version": version.version, "comment": comment},
            )
            session.commit()
            session.refresh(workflow)
            return workflow

    def rollback(
        self, workflow_id: uuid.UUID, target_version: int, actor: str = "human"
    ) -> Workflow:
        """One-call rollback: redeploy an old definition as a NEW version.

        Roll-forward semantics (see ADR-002): history stays append-only, so
        the audit trail shows the rollback instead of erasing what happened.
        """
        with self._session_factory() as session:
            workflow = self._get(session, workflow_id)
            target = session.execute(
                select(WorkflowVersion).where(
                    WorkflowVersion.workflow_id == workflow_id,
                    WorkflowVersion.version == target_version,
                )
            ).scalar_one_or_none()
            if target is None:
                raise VersionNotFoundError(
                    f"Workflow {workflow_id} has no version {target_version}"
                )

            new_version = self._add_version(
                session,
                workflow,
                target.definition,
                actor,
                comment=f"rollback to v{target_version}",
            )

            if workflow.engine_workflow_id is None:
                engine_wf = self._adapter.create_workflow(target.definition)
                workflow.engine_workflow_id = engine_wf.id
            else:
                self._adapter.update_workflow(
                    workflow.engine_workflow_id, target.definition
                )

            workflow.current_version = new_version.version
            self._audit(
                session,
                actor=actor,
                action="workflow.rollback",
                workflow=workflow,
                detail={
                    "from_version": target_version,
                    "as_version": new_version.version,
                },
            )
            session.commit()
            session.refresh(workflow)
            return workflow

    def set_active(
        self, workflow_id: uuid.UUID, active: bool, actor: str = "human"
    ) -> Workflow:
        with self._session_factory() as session:
            workflow = self._get(session, workflow_id)
            if workflow.engine_workflow_id is None:
                raise VersionNotFoundError(
                    f"Workflow {workflow_id} has never been deployed"
                )
            self._adapter.set_active(workflow.engine_workflow_id, active)
            workflow.status = (
                WorkflowStatus.ACTIVE if active else WorkflowStatus.INACTIVE
            )
            self._audit(
                session,
                actor=actor,
                action="workflow.activate" if active else "workflow.deactivate",
                workflow=workflow,
            )
            session.commit()
            session.refresh(workflow)
            return workflow

    def delete(self, workflow_id: uuid.UUID, actor: str = "human") -> None:
        """Remove the workflow from the engine — never silently destructive.

        The engine's live copy is snapshotted as a final version first (it
        could have drifted from the registry), then deleted. Registry rows
        are kept: history survives the delete.
        """
        with self._session_factory() as session:
            workflow = self._get(session, workflow_id)

            if workflow.engine_workflow_id is not None:
                live = self._adapter.get_workflow(workflow.engine_workflow_id)
                self._add_version(
                    session,
                    workflow,
                    live.definition,
                    actor,
                    comment="pre-delete backup",
                )
                self._adapter.delete_workflow(workflow.engine_workflow_id)
                workflow.engine_workflow_id = None

            workflow.status = WorkflowStatus.INACTIVE
            self._audit(
                session, actor=actor, action="workflow.delete", workflow=workflow
            )
            session.commit()

    # ── internals ────────────────────────────────────────────────────────

    @staticmethod
    def _get(session: Session, workflow_id: uuid.UUID) -> Workflow:
        workflow = session.get(Workflow, workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(f"No workflow {workflow_id}")
        return workflow

    @staticmethod
    def _add_version(
        session: Session,
        workflow: Workflow,
        definition: dict[str, Any],
        actor: str,
        comment: str | None,
    ) -> WorkflowVersion:
        max_version = session.execute(
            select(func.coalesce(func.max(WorkflowVersion.version), 0)).where(
                WorkflowVersion.workflow_id == workflow.id
            )
        ).scalar_one()
        version = WorkflowVersion(
            workflow_id=workflow.id,
            version=max_version + 1,
            definition=definition,
            created_by=actor,
            comment=comment,
        )
        session.add(version)
        session.flush()
        return version

    @staticmethod
    def _audit(
        session: Session,
        *,
        actor: str,
        action: str,
        workflow: Workflow,
        detail: dict[str, Any] | None = None,
    ) -> None:
        session.add(
            AuditLog(
                actor=actor,
                action=action,
                entity_type="workflow",
                entity_id=str(workflow.id),
                detail=detail,
            )
        )
