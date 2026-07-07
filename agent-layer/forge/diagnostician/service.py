"""The diagnostician service.

On a failed run: gather the execution data + current workflow definition,
ask the LLM for a root-cause analysis and (maybe) a patch, then:

- patch valid + LOW risk + auto-apply enabled → deploy it (the registry gives
  us the versioned backup and audit entry for free) and file a RESOLVED
  incident documenting what happened;
- patch valid + HIGH risk (or auto-apply disabled) → file an incident
  AWAITING_APPROVAL with the patch attached;
- no patch / invalid patch → file an OPEN incident with the analysis, which
  is the human-readable incident report.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from forge.db.models import (
    Incident,
    IncidentStatus,
    Run,
    Workflow,
    WorkflowVersion,
    utcnow,
)
from forge.diagnostician.prompts import SYSTEM_PROMPT, diagnosis_prompt
from forge.diagnostician.risk import assess_patch
from forge.jsonutil import extract_json_object
from forge.llm_gateway import LLMGateway
from forge.registry import WorkflowRegistry
from forge.validator import validate_workflow

logger = logging.getLogger(__name__)

SERVICE_NAME = "diagnostician"


class Diagnostician:
    def __init__(
        self,
        session_factory: sessionmaker,
        gateway: LLMGateway,
        registry: WorkflowRegistry,
        auto_apply: bool = True,
    ) -> None:
        self._session_factory = session_factory
        self._gateway = gateway
        self._registry = registry
        self._auto_apply = auto_apply

    def diagnose_run(self, run_id: uuid.UUID) -> Incident | None:
        """Analyze one failed run. Idempotent: an unresolved incident for the
        same run short-circuits, so the poller can call this repeatedly."""
        with self._session_factory() as session:
            run = session.get(Run, run_id)
            if run is None:
                logger.warning("diagnose_run: no run %s", run_id)
                return None

            existing: Incident | None = session.execute(
                select(Incident).where(
                    Incident.run_id == run_id,
                    Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.AWAITING_APPROVAL]),
                )
            ).scalar_one_or_none()
            if existing is not None:
                return existing

            workflow = session.get(Workflow, run.workflow_id)
            assert workflow is not None  # FK guarantees it
            definition = self._current_definition(session, workflow)
            error_message = run.error_message
            payload: dict[str, Any] = run.payload or {}
            workflow_id = workflow.id

        analysis = self._analyze(definition, payload, error_message)
        return self._settle(workflow_id, run_id, definition, analysis)

    def approve(self, incident_id: uuid.UUID, actor: str = "human") -> Incident:
        """Apply an awaiting patch — the one-call approval for high-risk repairs."""
        with self._session_factory() as session:
            incident = session.get(Incident, incident_id)
            if incident is None:
                raise IncidentNotFoundError(f"no incident {incident_id}")
            if incident.status != IncidentStatus.AWAITING_APPROVAL:
                raise IncidentStateError(
                    f"incident is {incident.status.value}, not awaiting_approval"
                )
            if not incident.proposed_patch:
                raise IncidentStateError("incident has no proposed patch to apply")
            workflow = session.get(Workflow, incident.workflow_id)
            assert workflow is not None
            patch = incident.proposed_patch
            workflow_name = workflow.name

        self._registry.deploy(
            name=str(patch.get("name", workflow_name)),
            definition=patch,
            workflow_id=incident.workflow_id,
            actor=actor,
            comment=f"approved patch for incident {incident_id}",
        )
        return self._close(incident_id, IncidentStatus.RESOLVED)

    def dismiss(self, incident_id: uuid.UUID) -> Incident:
        with self._session_factory() as session:
            incident = session.get(Incident, incident_id)
            if incident is None:
                raise IncidentNotFoundError(f"no incident {incident_id}")
        return self._close(incident_id, IncidentStatus.DISMISSED)

    # ── internals ────────────────────────────────────────────────────────

    def _analyze(
        self,
        definition: dict[str, Any],
        payload: dict[str, Any],
        error_message: str | None,
    ) -> dict[str, Any]:
        response = self._gateway.complete(
            prompt=diagnosis_prompt(definition, payload, error_message),
            system=SYSTEM_PROMPT,
            service=SERVICE_NAME,
            purpose="root-cause a failed run",
        )
        parsed, parse_error = extract_json_object(response.text)
        if parsed is None:
            # A useless analysis still becomes an incident — never a silent drop.
            return {
                "summary": f"diagnostician output unusable: {parse_error}",
                "root_cause": None,
                "patch": None,
            }
        return parsed

    def _settle(
        self,
        workflow_id: uuid.UUID,
        run_id: uuid.UUID,
        current_definition: dict[str, Any],
        analysis: dict[str, Any],
    ) -> Incident:
        summary = str(analysis.get("summary") or "workflow run failed")
        root_cause = analysis.get("root_cause")
        patch = analysis.get("patch")

        if not isinstance(patch, dict):
            return self._file_incident(
                workflow_id, run_id, IncidentStatus.OPEN, "medium", summary, root_cause, None
            )

        validation = validate_workflow(patch)
        if not validation.valid:
            return self._file_incident(
                workflow_id,
                run_id,
                IncidentStatus.OPEN,
                "medium",
                summary + " (proposed patch failed validation and was discarded)",
                root_cause,
                None,
            )

        risk = assess_patch(current_definition, patch)
        if risk.auto_applicable and self._auto_apply:
            self._registry.deploy(
                name=str(patch.get("name", current_definition.get("name", "workflow"))),
                definition=patch,
                workflow_id=workflow_id,
                actor=SERVICE_NAME,
                comment=f"auto-repair for run {run_id} (risk: low)",
            )
            incident = self._file_incident(
                workflow_id, run_id, IncidentStatus.RESOLVED, "low", summary, root_cause, patch
            )
            logger.info("run %s auto-repaired (incident %s)", run_id, incident.id)
            return incident

        return self._file_incident(
            workflow_id,
            run_id,
            IncidentStatus.AWAITING_APPROVAL,
            "high",
            summary + " — patch needs approval: " + "; ".join(risk.reasons),
            root_cause,
            patch,
        )

    def _file_incident(
        self,
        workflow_id: uuid.UUID,
        run_id: uuid.UUID,
        status: IncidentStatus,
        severity: str,
        summary: str,
        root_cause: Any,
        patch: dict[str, Any] | None,
    ) -> Incident:
        with self._session_factory() as session:
            incident = Incident(
                workflow_id=workflow_id,
                run_id=run_id,
                status=status,
                severity=severity,
                summary=summary,
                root_cause=str(root_cause) if root_cause else None,
                proposed_patch=patch,
                resolved_at=utcnow() if status == IncidentStatus.RESOLVED else None,
            )
            session.add(incident)
            session.commit()
            session.refresh(incident)
            return incident

    def _close(self, incident_id: uuid.UUID, status: IncidentStatus) -> Incident:
        with self._session_factory() as session:
            incident: Incident | None = session.get(Incident, incident_id)
            assert incident is not None  # callers checked existence
            incident.status = status
            incident.resolved_at = utcnow()
            session.commit()
            session.refresh(incident)
            return incident

    @staticmethod
    def _current_definition(session: Session, workflow: Workflow) -> dict[str, Any]:
        version = session.execute(
            select(WorkflowVersion).where(
                WorkflowVersion.workflow_id == workflow.id,
                WorkflowVersion.version == workflow.current_version,
            )
        ).scalar_one_or_none()
        return dict(version.definition) if version else {"name": workflow.name, "nodes": []}


class IncidentNotFoundError(Exception):
    pass


class IncidentStateError(Exception):
    pass
