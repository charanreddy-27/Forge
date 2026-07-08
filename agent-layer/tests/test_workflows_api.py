"""HTTP-level tests for the /workflows endpoints."""

import uuid

import pytest
from fastapi.testclient import TestClient

from forge.main import create_app
from tests.fake_engine import FakeEngineAdapter

DEFINITION = {
    "name": "digest",
    "nodes": [{"type": "cron"}],
    "connections": {},
    "settings": {},
}


@pytest.fixture()
def client(settings, session_factory):
    app = create_app(settings)
    with TestClient(app) as test_client:
        # Swap the real datastores/engine for test doubles after lifespan startup.
        app.state.session_factory = session_factory
        app.state.engine_adapter = FakeEngineAdapter()
        yield test_client


def deploy(client, name="digest") -> dict:
    response = client.post(
        "/workflows",
        json={"name": name, "definition": DEFINITION, "comment": "initial"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_deploy_then_list(client):
    created = deploy(client)
    assert created["current_version"] == 1
    assert created["engine_workflow_id"]

    listed = client.get("/workflows").json()
    assert [w["id"] for w in listed] == [created["id"]]


def test_versions_and_rollback_endpoints(client):
    workflow = deploy(client)
    workflow_id = workflow["id"]

    response = client.put(
        f"/workflows/{workflow_id}",
        json={"name": "digest", "definition": {**DEFINITION, "v": 2}},
    )
    assert response.status_code == 200
    assert response.json()["current_version"] == 2

    versions = client.get(f"/workflows/{workflow_id}/versions").json()
    assert [v["version"] for v in versions] == [2, 1]

    response = client.post(
        f"/workflows/{workflow_id}/rollback", json={"target_version": 1}
    )
    assert response.status_code == 200
    assert response.json()["current_version"] == 3  # roll-forward

    versions = client.get(f"/workflows/{workflow_id}/versions").json()
    assert versions[0]["comment"] == "rollback to v1"


def test_activate_deactivate_delete(client):
    workflow_id = deploy(client)["id"]

    assert (
        client.post(f"/workflows/{workflow_id}/activate").json()["status"] == "active"
    )
    assert (
        client.post(f"/workflows/{workflow_id}/deactivate").json()["status"]
        == "inactive"
    )
    assert client.delete(f"/workflows/{workflow_id}").status_code == 204

    # History survives the delete.
    versions = client.get(f"/workflows/{workflow_id}/versions").json()
    assert versions[0]["comment"] == "pre-delete backup"


def test_unknown_workflow_is_404(client):
    missing = uuid.uuid4()
    assert client.get(f"/workflows/{missing}").status_code == 404
    assert (
        client.post(
            f"/workflows/{missing}/rollback", json={"target_version": 1}
        ).status_code
        == 404
    )
