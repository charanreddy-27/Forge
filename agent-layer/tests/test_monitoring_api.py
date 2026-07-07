"""HTTP-level tests for runs/health/sync and incident endpoints."""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from forge.main import create_app
from tests.fake_engine import FakeEngineAdapter
from tests.fake_gateway import FakeGateway

DEFINITION = {
    "name": "digest",
    "nodes": [{"name": "Cron", "type": "n8n-nodes-base.scheduleTrigger", "parameters": {}}],
    "connections": {},
    "settings": {},
}

HIGH_RISK_PATCH = {
    **DEFINITION,
    "nodes": DEFINITION["nodes"]
    + [{"name": "Slack", "type": "n8n-nodes-base.slack", "parameters": {"channel": "#x"}}],
}


@pytest.fixture()
def client(settings, session_factory, monkeypatch):
    app = create_app(settings)
    with TestClient(app) as test_client:
        app.state.session_factory = session_factory
        app.state.engine_adapter = FakeEngineAdapter()
        # Incidents endpoints build a gateway; keep the real class out of tests.
        analysis = json.dumps({"summary": "s", "root_cause": "r", "patch": HIGH_RISK_PATCH})
        monkeypatch.setattr(
            "forge.api.incidents.LLMGateway", lambda *args, **kwargs: FakeGateway([analysis])
        )
        yield test_client


def deploy_and_fail_run(client) -> tuple[str, str]:
    workflow = client.post("/workflows", json={"name": "digest", "definition": DEFINITION}).json()
    engine: FakeEngineAdapter = client.app.state.engine_adapter
    engine.add_execution(workflow["engine_workflow_id"], "ex-1", "failed")
    sync = client.post("/monitor/sync").json()
    return workflow["id"], sync["newly_failed_runs"][0]


def test_sync_runs_and_health(client):
    workflow_id, _run_id = deploy_and_fail_run(client)

    runs = client.get(f"/workflows/{workflow_id}/runs").json()
    assert len(runs) == 1
    assert runs[0]["status"] == "failed"

    health = client.get(f"/workflows/{workflow_id}/health").json()
    assert health["status"] == "degraded"
    assert health["consecutive_failures"] == 1


def test_incident_approve_flow_over_http(client, session_factory):
    from forge.diagnostician import Diagnostician
    from forge.registry import WorkflowRegistry

    workflow_id, run_id = deploy_and_fail_run(client)

    # The worker would do this; drive it directly with a canned analysis.
    registry = WorkflowRegistry(session_factory, client.app.state.engine_adapter)
    analysis = json.dumps({"summary": "s", "root_cause": "r", "patch": HIGH_RISK_PATCH})
    diagnostician = Diagnostician(
        session_factory, FakeGateway([analysis]), registry  # type: ignore[arg-type]
    )
    diagnostician.diagnose_run(uuid.UUID(run_id))

    incidents = client.get("/incidents", params={"status": "awaiting_approval"}).json()
    assert len(incidents) == 1
    incident_id = incidents[0]["id"]
    assert incidents[0]["proposed_patch"] is not None

    approved = client.post(f"/incidents/{incident_id}/approve", json={"actor": "human:me"})
    assert approved.status_code == 200
    assert approved.json()["status"] == "resolved"
    assert client.get(f"/workflows/{workflow_id}").json()["current_version"] == 2

    # Approving twice conflicts.
    assert (
        client.post(f"/incidents/{incident_id}/approve", json={"actor": "human:me"}).status_code
        == 409
    )


def test_unknown_ids_are_404(client):
    missing = uuid.uuid4()
    assert client.get(f"/workflows/{missing}/runs").status_code == 404
    assert client.get(f"/workflows/{missing}/health").status_code == 404
    assert client.get(f"/incidents/{missing}").status_code == 404
    assert client.post(f"/incidents/{missing}/dismiss").status_code == 404
