"""Execution ingest + per-workflow health.

The engine (n8n) keeps its own execution log; the monitor mirrors it into the
`runs` table so Forge owns the history (the engine stays swappable and its
retention settings stop mattering), and so the diagnostician can be handed a
run row instead of a live engine query.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from forge.db.models import Run, RunStatus, Workflow, utcnow
from forge.engine_adapter import EngineAdapter, EngineExecution

# Health looks at the most recent N finished runs.
_HEALTH_WINDOW = 20


@dataclass(frozen=True)
class WorkflowHealth:
    workflow_id: uuid.UUID
    # healthy | degraded | failing | unknown
    status: str
    total_runs: int
    success_rate: float | None
    consecutive_failures: int
    last_run_status: str | None
    last_run_at: datetime | None

    def as_dict(self) -> dict:
        return {
            "workflow_id": str(self.workflow_id),
            "status": self.status,
            "total_runs": self.total_runs,
            "success_rate": self.success_rate,
            "consecutive_failures": self.consecutive_failures,
            "last_run_status": self.last_run_status,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
        }


class RunMonitor:
    def __init__(self, session_factory: sessionmaker, adapter: EngineAdapter) -> None:
        self._session_factory = session_factory
        self._adapter = adapter

    def sync_workflow(self, workflow_id: uuid.UUID, limit: int = 50) -> list[Run]:
        """Mirror the engine's executions for one workflow. Returns runs that
        are newly failed (created as failed, or transitioned to failed) —
        exactly the set the diagnostician should look at."""
        with self._session_factory() as session:
            workflow = session.get(Workflow, workflow_id)
            if workflow is None or workflow.engine_workflow_id is None:
                return []

            executions = self._adapter.list_executions(
                workflow.engine_workflow_id, limit=limit
            )
            newly_failed = [
                run
                for execution in executions
                if (run := self._upsert(session, workflow, execution)) is not None
            ]
            session.commit()
            for run in newly_failed:
                session.refresh(run)
            return newly_failed

    def sync_all(self, limit: int = 50) -> list[Run]:
        """Sync every deployed workflow; returns all newly failed runs."""
        with self._session_factory() as session:
            workflow_ids = (
                session.execute(
                    select(Workflow.id).where(Workflow.engine_workflow_id.is_not(None))
                )
                .scalars()
                .all()
            )
        failed: list[Run] = []
        for workflow_id in workflow_ids:
            failed.extend(self.sync_workflow(workflow_id, limit=limit))
        return failed

    def health(self, workflow_id: uuid.UUID) -> WorkflowHealth:
        with self._session_factory() as session:
            runs = (
                session.execute(
                    select(Run)
                    .where(Run.workflow_id == workflow_id)
                    .order_by(Run.started_at.desc())
                    .limit(_HEALTH_WINDOW)
                )
                .scalars()
                .all()
            )

        if not runs:
            return WorkflowHealth(workflow_id, "unknown", 0, None, 0, None, None)

        finished = [r for r in runs if r.status != RunStatus.RUNNING]
        successes = sum(1 for r in finished if r.status == RunStatus.SUCCESS)
        success_rate = round(successes / len(finished), 3) if finished else None

        consecutive_failures = 0
        for run in finished:
            if run.status != RunStatus.FAILED:
                break
            consecutive_failures += 1

        if consecutive_failures >= 2:
            status = "failing"
        elif consecutive_failures == 1 or (
            success_rate is not None and success_rate < 0.8
        ):
            status = "degraded"
        elif finished:
            status = "healthy"
        else:
            status = "unknown"  # only running executions so far

        return WorkflowHealth(
            workflow_id=workflow_id,
            status=status,
            total_runs=len(runs),
            success_rate=success_rate,
            consecutive_failures=consecutive_failures,
            last_run_status=runs[0].status.value,
            last_run_at=runs[0].started_at,
        )

    # ── internals ────────────────────────────────────────────────────────

    def _upsert(
        self, session: Session, workflow: Workflow, execution: EngineExecution
    ) -> Run | None:
        """Insert or update one run row; return it only if it's newly failed."""
        run = session.execute(
            select(Run).where(
                Run.workflow_id == workflow.id,
                Run.engine_execution_id == execution.id,
            )
        ).scalar_one_or_none()

        new_status = RunStatus(execution.status)
        if run is None:
            run = Run(
                workflow_id=workflow.id,
                engine_execution_id=execution.id,
                status=new_status,
                started_at=_parse_ts(execution.started_at) or utcnow(),
                finished_at=_parse_ts(execution.finished_at),
                payload=execution.data,
            )
            session.add(run)
            session.flush()
            return run if new_status == RunStatus.FAILED else None

        was_failed = run.status == RunStatus.FAILED
        run.status = new_status
        run.finished_at = _parse_ts(execution.finished_at)
        run.payload = execution.data
        session.flush()
        return run if new_status == RunStatus.FAILED and not was_failed else None


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
