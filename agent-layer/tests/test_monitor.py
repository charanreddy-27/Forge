"""Tests for the run monitor: ingest, failure transitions, health."""

import pytest

from forge.db.models import RunStatus
from forge.monitor import RunMonitor
from forge.registry import WorkflowRegistry
from tests.fake_engine import FakeEngineAdapter

DEFINITION = {
    "name": "digest",
    "nodes": [{"name": "Cron", "type": "n8n-nodes-base.scheduleTrigger", "parameters": {}}],
    "connections": {},
    "settings": {},
}


@pytest.fixture()
def env(session_factory):
    engine = FakeEngineAdapter()
    registry = WorkflowRegistry(session_factory, engine)
    workflow = registry.deploy(name="digest", definition=DEFINITION)
    monitor = RunMonitor(session_factory, engine)
    return engine, workflow, monitor


class TestSync:
    def test_ingests_executions_as_runs(self, env):
        engine, workflow, monitor = env
        engine.add_execution(workflow.engine_workflow_id, "1", "success")
        engine.add_execution(workflow.engine_workflow_id, "2", "failed")

        newly_failed = monitor.sync_workflow(workflow.id)

        assert [r.engine_execution_id for r in newly_failed] == ["2"]
        health = monitor.health(workflow.id)
        assert health.total_runs == 2

    def test_sync_is_idempotent(self, env):
        engine, workflow, monitor = env
        engine.add_execution(workflow.engine_workflow_id, "1", "failed")

        first = monitor.sync_workflow(workflow.id)
        second = monitor.sync_workflow(workflow.id)

        assert len(first) == 1
        assert second == []  # same failure isn't "new" twice
        assert monitor.health(workflow.id).total_runs == 1

    def test_running_to_failed_transition_is_reported(self, env):
        engine, workflow, monitor = env
        engine.add_execution(workflow.engine_workflow_id, "1", "running", finished_at=None)
        assert monitor.sync_workflow(workflow.id) == []

        engine.executions[workflow.engine_workflow_id] = []
        engine.add_execution(workflow.engine_workflow_id, "1", "failed")

        newly_failed = monitor.sync_workflow(workflow.id)
        assert len(newly_failed) == 1
        assert newly_failed[0].status == RunStatus.FAILED

    def test_sync_all_covers_every_deployed_workflow(self, env, session_factory):
        engine, workflow, monitor = env
        registry = WorkflowRegistry(session_factory, engine)
        other = registry.deploy(name="other", definition={**DEFINITION, "name": "other"})
        engine.add_execution(workflow.engine_workflow_id, "1", "failed")
        engine.add_execution(other.engine_workflow_id, "2", "failed")

        assert len(monitor.sync_all()) == 2


class TestHealth:
    def test_no_runs_is_unknown(self, env):
        _, workflow, monitor = env
        assert monitor.health(workflow.id).status == "unknown"

    def test_all_success_is_healthy(self, env):
        engine, workflow, monitor = env
        for i in range(5):
            engine.add_execution(workflow.engine_workflow_id, str(i), "success")
        monitor.sync_workflow(workflow.id)

        health = monitor.health(workflow.id)
        assert health.status == "healthy"
        assert health.success_rate == 1.0
        assert health.consecutive_failures == 0

    def test_single_recent_failure_is_degraded(self, env):
        engine, workflow, monitor = env
        # add_execution inserts at the front → "3" (failed) is the most recent.
        engine.add_execution(workflow.engine_workflow_id, "1", "success")
        engine.add_execution(workflow.engine_workflow_id, "2", "success")
        engine.add_execution(
            workflow.engine_workflow_id, "3", "failed", started_at="2026-07-07T02:00:00Z"
        )
        monitor.sync_workflow(workflow.id)

        health = monitor.health(workflow.id)
        assert health.status == "degraded"
        assert health.consecutive_failures == 1

    def test_consecutive_failures_is_failing(self, env):
        engine, workflow, monitor = env
        engine.add_execution(
            workflow.engine_workflow_id, "1", "success", started_at="2026-07-07T00:00:00Z"
        )
        engine.add_execution(
            workflow.engine_workflow_id, "2", "failed", started_at="2026-07-07T01:00:00Z"
        )
        engine.add_execution(
            workflow.engine_workflow_id, "3", "failed", started_at="2026-07-07T02:00:00Z"
        )
        monitor.sync_workflow(workflow.id)

        health = monitor.health(workflow.id)
        assert health.status == "failing"
        assert health.consecutive_failures == 2
        assert health.last_run_status == "failed"
