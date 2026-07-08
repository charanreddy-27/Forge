"""n8n implementation of the engine adapter, using n8n's public REST API v1.

This module is the only place in the codebase that may mention n8n.
Authentication is via the X-N8N-API-KEY header (created in the n8n UI under
Settings → API).
"""

from typing import Any

import httpx

from forge.engine_adapter.base import EngineAdapter, EngineExecution, EngineWorkflow
from forge.engine_adapter.errors import (
    EngineAuthError,
    EngineError,
    EngineNotFoundError,
)

# n8n's create/update endpoints accept exactly these top-level fields; anything
# else (id, active, tags, ...) is rejected, so we filter before sending.
_WRITABLE_FIELDS = ("name", "nodes", "connections", "settings")

# n8n execution statuses → Forge RunStatus values.
_STATUS_MAP = {
    "success": "success",
    "error": "failed",
    "crashed": "failed",
    "failed": "failed",
    "canceled": "canceled",
    "running": "running",
    "waiting": "running",
    "new": "running",
}


class N8nAdapter(EngineAdapter):
    """Talks to a self-hosted n8n over /api/v1."""

    def __init__(
        self, base_url: str, api_key: str, http_client: httpx.Client | None = None
    ) -> None:
        # Injectable client so tests can pass httpx.MockTransport.
        self._http = http_client or httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"X-N8N-API-KEY": api_key, "Accept": "application/json"},
            timeout=30,
        )

    # ── EngineAdapter interface ──────────────────────────────────────────

    def create_workflow(self, definition: dict[str, Any]) -> EngineWorkflow:
        payload = self._writable(definition)
        data = self._request("POST", "/api/v1/workflows", json=payload)
        return self._to_workflow(data)

    def update_workflow(
        self, engine_id: str, definition: dict[str, Any]
    ) -> EngineWorkflow:
        payload = self._writable(definition)
        data = self._request("PUT", f"/api/v1/workflows/{engine_id}", json=payload)
        return self._to_workflow(data)

    def get_workflow(self, engine_id: str) -> EngineWorkflow:
        data = self._request("GET", f"/api/v1/workflows/{engine_id}")
        return self._to_workflow(data)

    def delete_workflow(self, engine_id: str) -> None:
        self._request("DELETE", f"/api/v1/workflows/{engine_id}")

    def set_active(self, engine_id: str, active: bool) -> EngineWorkflow:
        action = "activate" if active else "deactivate"
        data = self._request("POST", f"/api/v1/workflows/{engine_id}/{action}")
        return self._to_workflow(data)

    def list_executions(self, engine_id: str, limit: int = 50) -> list[EngineExecution]:
        data = self._request(
            "GET",
            "/api/v1/executions",
            params={"workflowId": engine_id, "limit": limit},
        )
        return [self._to_execution(item) for item in data.get("data", [])]

    def get_execution(self, execution_id: str) -> EngineExecution:
        # includeData=true pulls node-level run data — what the Phase 4
        # diagnostician will need to root-cause failures.
        data = self._request(
            "GET", f"/api/v1/executions/{execution_id}", params={"includeData": "true"}
        )
        return self._to_execution(data)

    # ── internals ────────────────────────────────────────────────────────

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise EngineError(f"n8n unreachable: {exc}") from exc

        if response.status_code in (401, 403):
            raise EngineAuthError("n8n rejected the API key (check N8N_API_KEY)")
        if response.status_code == 404:
            raise EngineNotFoundError(f"{method} {path}: not found in n8n")
        if response.status_code >= 400:
            raise EngineError(
                f"{method} {path}: n8n returned {response.status_code}: "
                f"{response.text[:500]}"
            )
        if not response.content:
            return {}
        result: dict[str, Any] = response.json()
        return result

    @staticmethod
    def _writable(definition: dict[str, Any]) -> dict[str, Any]:
        payload = {k: definition[k] for k in _WRITABLE_FIELDS if k in definition}
        # n8n requires all four fields on create/update.
        payload.setdefault("settings", {})
        payload.setdefault("nodes", [])
        payload.setdefault("connections", {})
        return payload

    @staticmethod
    def _to_workflow(data: dict[str, Any]) -> EngineWorkflow:
        return EngineWorkflow(
            id=str(data["id"]),
            name=data.get("name", ""),
            active=bool(data.get("active", False)),
            definition=data,
        )

    @staticmethod
    def _to_execution(data: dict[str, Any]) -> EngineExecution:
        raw_status = data.get("status")
        if raw_status is None:
            # Older n8n versions have no status field; derive it.
            raw_status = "success" if data.get("finished") else "running"
        return EngineExecution(
            id=str(data["id"]),
            workflow_id=str(data.get("workflowId", "")),
            status=_STATUS_MAP.get(str(raw_status), "failed"),
            started_at=data.get("startedAt"),
            finished_at=data.get("stoppedAt"),
            data=data,
        )
