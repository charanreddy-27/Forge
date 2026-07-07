"""Diagnostician flow tests: auto-repair, approval gating, incident filing."""

import json

import pytest

from forge.db.models import IncidentStatus
from forge.diagnostician import Diagnostician
from forge.monitor import RunMonitor
from forge.registry import WorkflowRegistry
from tests.fake_engine import FakeEngineAdapter
from tests.fake_gateway import FakeGateway

DEFINITION = {
    "name": "digest",
    "nodes": [
        {"name": "Cron", "type": "n8n-nodes-base.scheduleTrigger", "parameters": {}},
        {
            "name": "Fetch",
            "type": "n8n-nodes-base.httpRequest",
            "parameters": {"url": "https://old.example.com", "method": "GET"},
        },
    ],
    "connections": {"Cron": {"main": [[{"node": "Fetch", "type": "main", "index": 0}]]}},
    "settings": {},
}

LOW_RISK_PATCH = {
    **DEFINITION,
    "nodes": [
        DEFINITION["nodes"][0],
        {
            "name": "Fetch",
            "type": "n8n-nodes-base.httpRequest",
            "parameters": {"url": "https://new.example.com", "method": "GET"},
        },
    ],
}

HIGH_RISK_PATCH = {
    **DEFINITION,
    "nodes": DEFINITION["nodes"]
    + [{"name": "Slack", "type": "n8n-nodes-base.slack", "parameters": {"channel": "#x"}}],
}


def analysis(patch) -> str:
    return json.dumps(
        {
            "summary": "the fetch URL 404s",
            "root_cause": "node Fetch calls a dead URL",
            "patch": patch,
        }
    )


@pytest.fixture()
def env(session_factory):
    engine = FakeEngineAdapter()
    registry = WorkflowRegistry(session_factory, engine)
    workflow = registry.deploy(name="digest", definition=DEFINITION)
    monitor = RunMonitor(session_factory, engine)
    engine.add_execution(workflow.engine_workflow_id, "ex-1", "failed")
    failed_run = monitor.sync_workflow(workflow.id)[0]
    return engine, registry, workflow, failed_run


def make_diagnostician(session_factory, registry, llm_text: str, auto_apply=True):
    return Diagnostician(
        session_factory=session_factory,
        gateway=FakeGateway([llm_text]),  # type: ignore[arg-type]
        registry=registry,
        auto_apply=auto_apply,
    )


class TestAutoRepair:
    def test_low_risk_patch_is_applied_and_resolved(self, session_factory, env):
        engine, registry, workflow, run = env
        diagnostician = make_diagnostician(session_factory, registry, analysis(LOW_RISK_PATCH))

        incident = diagnostician.diagnose_run(run.id)

        assert incident.status == IncidentStatus.RESOLVED
        assert incident.severity == "low"
        # Patch deployed as version 2 — versioned backup + audit via the registry.
        assert registry.get_workflow(workflow.id).current_version == 2
        deployed = engine.workflows[workflow.engine_workflow_id].definition
        assert deployed["nodes"][1]["parameters"]["url"] == "https://new.example.com"
        versions = registry.list_versions(workflow.id)
        assert versions[0].created_by == "diagnostician"

    def test_auto_apply_disabled_parks_even_low_risk(self, session_factory, env):
        _, registry, workflow, run = env
        diagnostician = make_diagnostician(
            session_factory, registry, analysis(LOW_RISK_PATCH), auto_apply=False
        )

        incident = diagnostician.diagnose_run(run.id)

        assert incident.status == IncidentStatus.AWAITING_APPROVAL
        assert registry.get_workflow(workflow.id).current_version == 1  # untouched


class TestApprovalGate:
    def test_high_risk_patch_awaits_approval(self, session_factory, env):
        _, registry, workflow, run = env
        diagnostician = make_diagnostician(session_factory, registry, analysis(HIGH_RISK_PATCH))

        incident = diagnostician.diagnose_run(run.id)

        assert incident.status == IncidentStatus.AWAITING_APPROVAL
        assert incident.severity == "high"
        assert incident.proposed_patch is not None
        assert registry.get_workflow(workflow.id).current_version == 1  # NOT applied

    def test_approve_applies_patch_and_resolves(self, session_factory, env):
        engine, registry, workflow, run = env
        diagnostician = make_diagnostician(session_factory, registry, analysis(HIGH_RISK_PATCH))
        incident = diagnostician.diagnose_run(run.id)

        approved = diagnostician.approve(incident.id, actor="human:me")

        assert approved.status == IncidentStatus.RESOLVED
        assert registry.get_workflow(workflow.id).current_version == 2
        deployed = engine.workflows[workflow.engine_workflow_id].definition
        assert any(node["name"] == "Slack" for node in deployed["nodes"])

    def test_dismiss_leaves_workflow_untouched(self, session_factory, env):
        _, registry, workflow, run = env
        diagnostician = make_diagnostician(session_factory, registry, analysis(HIGH_RISK_PATCH))
        incident = diagnostician.diagnose_run(run.id)

        dismissed = diagnostician.dismiss(incident.id)

        assert dismissed.status == IncidentStatus.DISMISSED
        assert registry.get_workflow(workflow.id).current_version == 1


class TestIncidentReports:
    def test_no_patch_files_open_incident(self, session_factory, env):
        _, registry, _, run = env
        text = json.dumps(
            {"summary": "remote API is down", "root_cause": "external outage", "patch": None}
        )
        diagnostician = make_diagnostician(session_factory, registry, text)

        incident = diagnostician.diagnose_run(run.id)

        assert incident.status == IncidentStatus.OPEN
        assert incident.proposed_patch is None
        assert incident.root_cause == "external outage"

    def test_invalid_patch_is_discarded_not_applied(self, session_factory, env):
        _, registry, workflow, run = env
        bad_patch = {**LOW_RISK_PATCH, "nodes": [{"name": "X", "type": "evil.node"}]}
        diagnostician = make_diagnostician(session_factory, registry, analysis(bad_patch))

        incident = diagnostician.diagnose_run(run.id)

        assert incident.status == IncidentStatus.OPEN
        assert "failed validation" in incident.summary
        assert registry.get_workflow(workflow.id).current_version == 1

    def test_unusable_llm_output_still_files_incident(self, session_factory, env):
        _, registry, _, run = env
        diagnostician = make_diagnostician(session_factory, registry, "no json here")

        incident = diagnostician.diagnose_run(run.id)

        assert incident.status == IncidentStatus.OPEN
        assert "unusable" in incident.summary

    def test_diagnosis_is_idempotent_per_run(self, session_factory, env):
        _, registry, _, run = env
        diagnostician = make_diagnostician(session_factory, registry, analysis(HIGH_RISK_PATCH))

        first = diagnostician.diagnose_run(run.id)
        second = diagnostician.diagnose_run(run.id)

        assert first.id == second.id  # no duplicate incidents from re-polling
