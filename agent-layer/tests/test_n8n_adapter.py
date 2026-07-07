"""N8nAdapter tests against a mocked n8n REST API (httpx.MockTransport)."""

import json

import httpx
import pytest

from forge.engine_adapter import (
    EngineAuthError,
    EngineError,
    EngineNotFoundError,
    N8nAdapter,
)

BASE = "http://n8n.test"


def make_adapter(handler) -> tuple[N8nAdapter, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    def recording_handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    client = httpx.Client(
        base_url=BASE,
        headers={"X-N8N-API-KEY": "test-key"},
        transport=httpx.MockTransport(recording_handler),
    )
    return N8nAdapter(BASE, "test-key", http_client=client), requests


WORKFLOW_JSON = {
    "id": "wf-123",
    "name": "Daily digest",
    "active": False,
    "nodes": [{"type": "n8n-nodes-base.cron", "name": "Cron"}],
    "connections": {},
    "settings": {},
}


class TestWorkflowLifecycle:
    def test_create_sends_only_writable_fields(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.url.path == "/api/v1/workflows"
            body = json.loads(request.content)
            # n8n rejects extra fields like id/active — adapter must strip them.
            assert set(body) == {"name", "nodes", "connections", "settings"}
            return httpx.Response(200, json=WORKFLOW_JSON)

        adapter, requests = make_adapter(handler)
        definition = {**WORKFLOW_JSON, "active": True, "extraneous": "x"}
        workflow = adapter.create_workflow(definition)

        assert workflow.id == "wf-123"
        assert workflow.name == "Daily digest"
        assert requests[0].headers["X-N8N-API-KEY"] == "test-key"

    def test_update_puts_to_workflow_path(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "PUT"
            assert request.url.path == "/api/v1/workflows/wf-123"
            return httpx.Response(200, json=WORKFLOW_JSON)

        adapter, _ = make_adapter(handler)
        assert adapter.update_workflow("wf-123", WORKFLOW_JSON).id == "wf-123"

    def test_get_and_delete(self):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, json=WORKFLOW_JSON)
            assert request.method == "DELETE"
            return httpx.Response(200, json=WORKFLOW_JSON)

        adapter, _ = make_adapter(handler)
        assert adapter.get_workflow("wf-123").definition["nodes"]
        adapter.delete_workflow("wf-123")  # must not raise

    def test_activate_and_deactivate_paths(self):
        paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            paths.append(request.url.path)
            return httpx.Response(200, json={**WORKFLOW_JSON, "active": True})

        adapter, _ = make_adapter(handler)
        assert adapter.set_active("wf-123", True).active is True
        adapter.set_active("wf-123", False)
        assert paths == [
            "/api/v1/workflows/wf-123/activate",
            "/api/v1/workflows/wf-123/deactivate",
        ]


class TestExecutions:
    def test_list_executions_maps_statuses(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/executions"
            assert request.url.params["workflowId"] == "wf-123"
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"id": 1, "workflowId": "wf-123", "status": "success"},
                        {"id": 2, "workflowId": "wf-123", "status": "error"},
                        {"id": 3, "workflowId": "wf-123", "status": "waiting"},
                    ]
                },
            )

        adapter, _ = make_adapter(handler)
        executions = adapter.list_executions("wf-123")
        assert [e.status for e in executions] == ["success", "failed", "running"]

    def test_get_execution_requests_run_data(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/v1/executions/42"
            assert request.url.params["includeData"] == "true"
            return httpx.Response(
                200,
                json={
                    "id": 42,
                    "workflowId": "wf-123",
                    "finished": True,
                    "startedAt": "2026-07-07T00:00:00Z",
                    "stoppedAt": "2026-07-07T00:00:05Z",
                },
            )

        adapter, _ = make_adapter(handler)
        execution = adapter.get_execution("42")
        # No status field (older n8n) → derived from `finished`.
        assert execution.status == "success"
        assert execution.finished_at == "2026-07-07T00:00:05Z"


class TestErrors:
    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (401, EngineAuthError),
            (403, EngineAuthError),
            (404, EngineNotFoundError),
            (500, EngineError),
        ],
    )
    def test_http_errors_map_to_engine_errors(self, status, expected):
        adapter, _ = make_adapter(lambda request: httpx.Response(status, text="boom"))
        with pytest.raises(expected):
            adapter.get_workflow("wf-123")

    def test_network_failure_raises_engine_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        adapter, _ = make_adapter(handler)
        with pytest.raises(EngineError, match="unreachable"):
            adapter.get_workflow("wf-123")
