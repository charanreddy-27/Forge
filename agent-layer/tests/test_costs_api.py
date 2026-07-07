"""Tests for the /costs/summary endpoint."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from forge.db.models import LLMCall
from forge.main import create_app
from tests.fake_engine import FakeEngineAdapter


@pytest.fixture()
def client(settings, session_factory):
    app = create_app(settings)
    with TestClient(app) as test_client:
        app.state.session_factory = session_factory
        app.state.engine_adapter = FakeEngineAdapter()
        yield test_client


def add_call(session_factory, service: str, cost: str, days_ago: int = 0) -> None:
    with session_factory() as session:
        session.add(
            LLMCall(
                provider="anthropic",
                model="claude-opus-4-8",
                service=service,
                purpose="test",
                cost_usd=Decimal(cost),
                created_at=datetime.now(UTC) - timedelta(days=days_ago),
            )
        )
        session.commit()


def test_summary_groups_by_day_and_service(client, session_factory):
    add_call(session_factory, "workflow-generator", "0.10", days_ago=0)
    add_call(session_factory, "workflow-generator", "0.20", days_ago=0)
    add_call(session_factory, "diagnostician", "0.05", days_ago=1)

    body = client.get("/costs/summary?days=7").json()

    assert body["budget_usd"] == 10.0
    assert body["spend_today_usd"] == pytest.approx(0.30)
    assert len(body["daily"]) == 2
    assert sum(day["cost_usd"] for day in body["daily"]) == pytest.approx(0.35)

    services = {row["service"]: row for row in body["by_service"]}
    assert services["workflow-generator"]["cost_usd"] == pytest.approx(0.30)
    assert services["workflow-generator"]["calls"] == 2
    assert services["diagnostician"]["cost_usd"] == pytest.approx(0.05)


def test_summary_empty_database(client):
    body = client.get("/costs/summary").json()
    assert body["daily"] == []
    assert body["by_service"] == []
    assert body["spend_today_usd"] == 0.0
