"""HTTP-level tests for the /generate endpoints."""

import pytest
from fastapi.testclient import TestClient

from forge.jobs.queue import JobQueue
from forge.main import create_app
from tests.fake_redis import FakeRedis


@pytest.fixture()
def client_and_queue(settings, session_factory):
    app = create_app(settings)
    fake_redis = FakeRedis()
    with TestClient(app) as test_client:
        app.state.session_factory = session_factory
        app.state.redis = fake_redis
        yield test_client, JobQueue(fake_redis)


def test_submit_returns_202_and_job_is_queued(client_and_queue):
    client, queue = client_and_queue
    response = client.post(
        "/generate",
        json={"instruction": "email me a daily digest of my RSS feed", "deploy": True},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    record = queue.get(job_id)
    assert record["status"] == "queued"
    assert record["payload"]["deploy"] is True
    assert record["payload"]["allow_destructive"] is False  # default: gated


def test_poll_job_status_and_result(client_and_queue):
    client, queue = client_and_queue
    job_id = client.post("/generate", json={"instruction": "watch my feed"}).json()[
        "job_id"
    ]

    # Simulate the worker completing the job.
    claimed_id, _ = queue.claim(timeout=1)
    assert claimed_id == job_id
    queue.finish(job_id, "succeeded", {"definition": {"name": "x"}})

    body = client.get(f"/generate/{job_id}").json()
    assert body["status"] == "succeeded"
    assert body["result"]["definition"] == {"name": "x"}


def test_unknown_job_is_404(client_and_queue):
    client, _ = client_and_queue
    assert client.get("/generate/doesnotexist").status_code == 404


def test_instruction_too_short_is_422(client_and_queue):
    client, _ = client_and_queue
    assert client.post("/generate", json={"instruction": "hi"}).status_code == 422
