"""WorkflowRegistry tests: versioned deploys, rollback, audited deletes."""

import uuid

import pytest
from sqlalchemy import select

from forge.db.models import AuditLog, WorkflowStatus, WorkflowVersion
from forge.registry import VersionNotFoundError, WorkflowNotFoundError, WorkflowRegistry
from tests.fake_engine import FakeEngineAdapter

DEF_V1 = {
    "name": "digest",
    "nodes": [{"type": "cron"}],
    "connections": {},
    "settings": {},
}
DEF_V2 = {
    "name": "digest",
    "nodes": [{"type": "cron"}, {"type": "http"}],
    "connections": {},
}


@pytest.fixture()
def engine() -> FakeEngineAdapter:
    return FakeEngineAdapter()


@pytest.fixture()
def registry(session_factory, engine) -> WorkflowRegistry:
    return WorkflowRegistry(session_factory=session_factory, adapter=engine)


class TestDeploy:
    def test_first_deploy_creates_v1_in_registry_and_engine(self, registry, engine):
        workflow = registry.deploy(name="digest", definition=DEF_V1, actor="human")

        assert workflow.current_version == 1
        assert workflow.status == WorkflowStatus.INACTIVE  # deployed, not yet activated
        assert workflow.engine_workflow_id in engine.workflows
        assert engine.calls == [("create", workflow.engine_workflow_id)]

    def test_redeploy_appends_v2_and_updates_engine(self, registry, engine):
        workflow = registry.deploy(name="digest", definition=DEF_V1)
        workflow = registry.deploy(
            name="digest",
            definition=DEF_V2,
            workflow_id=workflow.id,
            actor="workflow-generator",
        )

        assert workflow.current_version == 2
        assert engine.workflows[workflow.engine_workflow_id].definition == DEF_V2
        versions = registry.list_versions(workflow.id)
        assert [v.version for v in versions] == [2, 1]
        assert versions[0].created_by == "workflow-generator"

    def test_failed_engine_call_stores_nothing(self, registry, engine, session_factory):
        def explode(definition):
            raise RuntimeError("engine down")

        engine.create_workflow = explode  # type: ignore[method-assign]

        with pytest.raises(RuntimeError):
            registry.deploy(name="digest", definition=DEF_V1)

        with session_factory() as session:
            assert session.execute(select(WorkflowVersion)).scalars().all() == []

    def test_deploy_writes_audit_entry(self, registry, session_factory):
        workflow = registry.deploy(name="digest", definition=DEF_V1)

        with session_factory() as session:
            entry = session.execute(
                select(AuditLog).where(AuditLog.action == "workflow.deploy")
            ).scalar_one()
        assert entry.entity_id == str(workflow.id)
        assert entry.detail["version"] == 1


class TestRollback:
    def test_rollback_is_one_call_and_rolls_forward(self, registry, engine):
        workflow = registry.deploy(name="digest", definition=DEF_V1)
        registry.deploy(name="digest", definition=DEF_V2, workflow_id=workflow.id)

        workflow = registry.rollback(workflow.id, target_version=1)

        # v1's definition redeployed as a NEW version 3 — history stays append-only.
        assert workflow.current_version == 3
        versions = registry.list_versions(workflow.id)
        assert versions[0].definition == DEF_V1
        assert versions[0].comment == "rollback to v1"
        assert engine.workflows[workflow.engine_workflow_id].definition == DEF_V1

    def test_rollback_to_missing_version_raises(self, registry):
        workflow = registry.deploy(name="digest", definition=DEF_V1)
        with pytest.raises(VersionNotFoundError):
            registry.rollback(workflow.id, target_version=99)

    def test_rollback_writes_audit_entry(self, registry, session_factory):
        workflow = registry.deploy(name="digest", definition=DEF_V1)
        registry.deploy(name="digest", definition=DEF_V2, workflow_id=workflow.id)
        registry.rollback(workflow.id, target_version=1, actor="diagnostician")

        with session_factory() as session:
            entry = session.execute(
                select(AuditLog).where(AuditLog.action == "workflow.rollback")
            ).scalar_one()
        assert entry.actor == "diagnostician"
        assert entry.detail == {"from_version": 1, "as_version": 3}


class TestActivateAndDelete:
    def test_activate_flips_status_and_engine_state(self, registry, engine):
        workflow = registry.deploy(name="digest", definition=DEF_V1)
        workflow = registry.set_active(workflow.id, True)

        assert workflow.status == WorkflowStatus.ACTIVE
        assert engine.workflows[workflow.engine_workflow_id].active is True

        workflow = registry.set_active(workflow.id, False)
        assert workflow.status == WorkflowStatus.INACTIVE

    def test_delete_snapshots_live_definition_first(
        self, registry, engine, session_factory
    ):
        workflow = registry.deploy(name="digest", definition=DEF_V1)
        engine_id = workflow.engine_workflow_id
        # Simulate drift: someone changed the workflow in the engine directly.
        engine.update_workflow(engine_id, {**DEF_V1, "drifted": True})

        registry.delete(workflow.id)

        assert engine_id not in engine.workflows  # gone from the engine
        versions = registry.list_versions(workflow.id)
        assert versions[0].comment == "pre-delete backup"
        assert versions[0].definition["drifted"] is True  # backup captured the drift

        with session_factory() as session:
            actions = session.execute(select(AuditLog.action)).scalars().all()
        assert "workflow.delete" in actions

    def test_unknown_workflow_raises(self, registry):
        with pytest.raises(WorkflowNotFoundError):
            registry.get_workflow(uuid.uuid4())
