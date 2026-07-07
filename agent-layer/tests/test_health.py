"""Tests for the /health endpoint."""

from fastapi.testclient import TestClient

import forge.main as main_module
from forge.main import create_app


def test_health_ok(settings, session_factory, monkeypatch):
    app = create_app(settings)
    # Skip real datastore connections: point the app at the SQLite test DB
    # and pretend Redis answers PONG.
    monkeypatch.setattr(main_module, "_check_redis", lambda _settings: True)
    with TestClient(app) as client:
        app.state.session_factory = session_factory
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] is True
    assert body["redis"] is True


def test_health_degraded_when_redis_down(settings, session_factory, monkeypatch):
    app = create_app(settings)
    monkeypatch.setattr(main_module, "_check_redis", lambda _settings: False)
    with TestClient(app) as client:
        app.state.session_factory = session_factory
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["redis"] is False
